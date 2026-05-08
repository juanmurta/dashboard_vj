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
# Adicione novas queries abaixo conforme for criando mais relatórios.
# Exemplo de estrutura para uma futura query:
# -----------------------------------------------------------------------------
# SQL_CLIENTES_ATIVOS = """
#     SELECT codcli, noment, cidade
#     FROM cliente
#     WHERE ativo = 'S'
#     ORDER BY noment
# """
