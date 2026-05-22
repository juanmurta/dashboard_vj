# =============================================================================
# database/queries.py — Repositório central de todas as queries SQL
# =============================================================================
# NUNCA espalhe SQL pelo código. Centralize tudo aqui.
# Benefícios:
#   - Fácil de encontrar e editar uma query
#   - Reutilização entre diferentes relatórios
#   - Histórico de alterações claro no Git
# =============================================================================


# -----------------------------------------------------------------------------
# QUERY PRINCIPAL: Notas de Saída (Pedidos/Vendas)
# -----------------------------------------------------------------------------
# Parâmetros obrigatórios:
#   :pcodemp  → Código da coligada/empresa (inteiro)
#   :pdatai   → Data inicial do período (string 'YYYY-MM-DD' ou date)
#   :pdataf   → Data final do período   (string 'YYYY-MM-DD' ou date)
#
# Retorna uma linha por nota emitida no período.
# -----------------------------------------------------------------------------
SQL_NOTAS_SAIDA = """
    SELECT
        s.cod_emp       AS COLIGADA,
        s.codcli        AS CODCLI,
        s.noment        AS NOMECLI,
        s.numped        AS PEDIDO,
        s.nota          AS NOTA,
        s.modelo        AS MODELO,
        s.dat_emi       AS DAT_EMI,
        s.dat_che       AS DAT_CHE,
        s.valor         AS VALOR,
        s.fechado       AS FECHADO,
        s.codfun        AS CODFUN,
        funcionario.nomfun  AS NOMFUN,
        s.cidendent     AS CIDADE,
        tipvenda.descricao  AS CLASSIFICACAO,
        formapag.despag     AS FORMAPAG,
        tipoconta.destip    AS TIPODOC,
        s.notcan        AS CANCELADO
    FROM sainota s
    INNER JOIN tipvenda   ON tipvenda.codigo   = s.tipvenda
    INNER JOIN funcionario ON funcionario.codfun = s.codfun
    INNER JOIN formapag   ON formapag.codpag   = s.codpag
    INNER JOIN tipoconta  ON tipoconta.codtip  = s.codtip
    WHERE
        s.cod_emp = :pcodemp
        AND s.dat_emi BETWEEN :pdatai AND :pdataf
    ORDER BY
        s.dat_emi, s.nota
"""


# -----------------------------------------------------------------------------
# QUERY: Produtos sem Giro
# -----------------------------------------------------------------------------
# Parâmetros obrigatórios:
#   :codemp  → Código da coligada/empresa (string, ex: '001')
#   :DIAS    → Quantidade de dias para trás (inteiro negativo, ex: -90)
#
# Retorna produtos com estoque > 0 que não tiveram saída nos últimos X dias.
# -----------------------------------------------------------------------------
SQL_PRODUTOS_SEM_GIRO = """
    SELECT
        produto.codpro,
        produto.despro,
        grupo.descricao as GRUPO,
        subgrupo.descricao as SUBGRUPO, 
        estoque.estoque,
        estoque.venda as PRECO_VENDA,
        estoque.custo as PRECO_CUSTO
    FROM estoque
    INNER JOIN produto  ON estoque.codpro = produto.codpro
    INNER JOIN grupo    ON produto.grupo  = grupo.codigo
    INNER JOIN subgrupo ON produto.subgrupo = subgrupo.subgrupo AND grupo.codigo = subgrupo.grupo
    WHERE
        estoque.estoque > 0
        AND produto.codpro NOT IN (
            SELECT s1.codpro
            FROM sainota s
            INNER JOIN sainota1 s1 ON s.id = s1.id AND s.cod_emp = s1.cod_emp
            INNER JOIN tipvenda t  ON s.tipvenda = t.codigo
            WHERE
                s.dat_che >= DATEADD(:DIAS DAY TO CURRENT_DATE)
                AND s.cod_emp = :codemp
                AND s.fechado = 'S'
                AND s.notcan = 'N'
                AND t.entramovimento = 'S'
        )
    ORDER BY
        3, 1
"""

# -----------------------------------------------------------------------------
# QUERY: Movimento de Caixas
# -----------------------------------------------------------------------------
# Parâmetros obrigatórios:
#   :pcodemp  → Código da coligada/empresa (inteiro)
#   :pdatai   → Data inicial (string 'YYYY-MM-DD')
#   :pdataf   → Data final (string 'YYYY-MM-DD')
# -----------------------------------------------------------------------------
SQL_MOVIMENTO_CAIXAS = """
    SELECT CAMOV.CODEMP AS CONTA, CADBANCO.banco AS NOME_ORIGEM, CAMOV.DATAMOV, CAMOV.CONTA,
           CADPLACON.DESCRICAO AS PLANO_DE_CONTA, CAMOV.VALOR,
           CAMOV.DC, CAMOV.HISTORICO, CAMOV.DESCRICAO
    FROM CAMOV
    INNER JOIN CADPLACON ON CAMOV.CONTA = CADPLACON.CODIGO
    INNER JOIN CADBANCO ON CADBANCO.conta = CAMOV.codemp
    WHERE CAMOV.DATAMOV BETWEEN :pdatai AND :pdataf
    AND CAMOV.EXCLUIDO = 'N'
    ORDER BY CAMOV.DATAMOV
"""

# -----------------------------------------------------------------------------
# QUERY: Posição de Estoque vs. Vendas
# -----------------------------------------------------------------------------
# Parâmetros obrigatórios:
#   :COLIGADA → Código da coligada/empresa (string, ex: '001')
#
# Retorna posição de estoque comparada com vendas dos últimos 180 dias.
# -----------------------------------------------------------------------------
SQL_POSICAO_ESTOQUE_VENDAS = """
    select  produto.codpro, produto.despro, estoque.datcad,
    produto.coduni, grupo.descricao as Grupo, subgrupo.descricao as subGrupo,
    estoque.estoque,estoque.estmin, estoque.medio, (estoque.estoque * estoque.medio) as CustoTotal,
    sum(sainota1.quant) TotalVenda,
    sum(sainota1.quant / 6) MediaEstoque
    from estoque
    inner join produto on produto.codpro = estoque.codpro
    left outer join grupo on produto.grupo = grupo.codigo
    left outer join subgrupo on grupo.codigo = subgrupo.grupo
    and produto.subgrupo = subgrupo.subgrupo
    left outer join sainota1 on sainota1.codpro = estoque.codpro
    inner join sainota on sainota1.id = sainota.id and estoque.cod_emp = sainota.cod_emp
    and sainota.fechado ='S'
    and sainota.notcan ='N'
    inner join tipvenda on sainota.tipvenda = tipvenda.codigo
    and tipvenda.entramovimento = 'S'
    and sainota.dat_Che >= DATEADD( - 180 DAY TO CURRENT_DATE )  --se quiser por ano mudar de 180 para 365
    where estoque.cod_emp = :COLIGADA
    and estoque.estoque > 0
    and estoque.ativo ='S'
    group by produto.codpro, produto.despro, estoque.datcad,
    produto.coduni, grupo.descricao,  subgrupo.descricao,
    estoque.estoque,estoque.estmin, estoque.medio
    order by 1
"""

# -----------------------------------------------------------------------------
# QUERY: Inadimplência Período
# -----------------------------------------------------------------------------
# Parâmetros obrigatórios:
#   :COLIGADA    → Código da coligada/empresa (inteiro)
#   :DATVEN_INI  → Data de vencimento inicial (string 'YYYY-MM-DD')
#   :DATVEN_FIN  → Data de vencimento final (string 'YYYY-MM-DD')
# -----------------------------------------------------------------------------
SQL_INADIMPLENCIA_PERIODO = """
    select caconrec.datemi, CACONREC.numdoc, sainota.nota, caconrec.datven,
    CACONREC.codrec, CACONREC.nomcli, CACONREC.cidcli, CACONREC.ufcli,
    CACONREC.codfun, funcionario.nomfun, sainota.codpag,
    formapag.despag,tipoconta.destip, caconrec.vrlcont ,  caconrec.valjur,
    (current_date - cast(caconrec.datven as date)) as DiasAtraso
    from Caconrec
    inner join funcionario on caconrec.codfun = funcionario.codfun
    inner join tipoconta on caconrec.tipdoc = tipoconta.codtip
    left outer join sainota on caconrec.idped = sainota.id
    and sainota.cod_emp = caconrec.codemp
    left outer join formapag on sainota.codpag = formapag.codpag
    where caconrec.codemp = :COLIGADA
    and caconrec.datven BETWEEN :DATVEN_INI AND :DATVEN_FIN
    and caconrec.pr = 0
    and caconrec.DATQUI IS NULL
"""

# -----------------------------------------------------------------------------
# Adicione novas queries abaixo conforme for criando mais relatórios.
# Exemplo de estrutura para uma futura query:
# -----------------------------------------------------------------------------
# SQL_CLIENTES_ATIVOS = """
#     SELECT codcli, noment, cidade
#     FROM cliente
#     WHERE ativo = 'S'
#     ORDER BY noment
# """
