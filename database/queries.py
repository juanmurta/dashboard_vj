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
# Adicione novas queries abaixo conforme for criando mais relatórios.
# Exemplo de estrutura para uma futura query:
# -----------------------------------------------------------------------------
# SQL_CLIENTES_ATIVOS = """
#     SELECT codcli, noment, cidade
#     FROM cliente
#     WHERE ativo = 'S'
#     ORDER BY noment
# """
