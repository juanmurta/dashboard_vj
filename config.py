# =============================================================================
# config.py — Configurações centrais da aplicação
# =============================================================================
# Todas as configurações ficam aqui: banco de dados, layout, cores, etc.
# Altere este arquivo para adaptar ao seu ambiente sem mexer no resto do código.
# =============================================================================

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES DO BANCO DE DADOS FIREBIRD
# -----------------------------------------------------------------------------
DB_CONFIG = {
    # Endereço IP do servidor onde o Firebird está rodando
    "host": "192.168.1.110",

    # Porta padrão do Firebird (3050). Altere se usar porta customizada.
    "port": 3050,

    # Caminho COMPLETO do arquivo .FDB no servidor remoto
    "database": r"C:\Makemoney\Dados\VISAWORK.FDB",

    # Usuário do banco (padrão Firebird: SYSDBA)
    "user": "SYSDBA",

    # Senha do banco
    "password": "masterkey",

    # Charset do banco — muito importante para acentuação correta!
    # Use WIN1252 para bancos Firebird brasileiros antigos, ou UTF8 para modernos.
    "charset": "WIN1252",
}

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES DA APLICAÇÃO DASH
# -----------------------------------------------------------------------------
APP_CONFIG = {
    # Título que aparece na aba do navegador
    "title": "Vieira JR — Painel de Relatórios",

    # Porta onde o servidor Dash vai rodar
    # Acesse em: http://localhost:8050 ou http://IP_DO_PC:8050
    "port": 8050,

    # debug=True recarrega automaticamente ao salvar arquivos (útil no desenvolvimento)
    # Mude para False em produção!
    "debug": True,

    # Se True, qualquer máquina na rede pode acessar o painel
    "host": "0.0.0.0",
}

# -----------------------------------------------------------------------------
# PALETA DE CORES DOS GRÁFICOS
# -----------------------------------------------------------------------------
# Cores usadas nos gráficos Plotly. Personalize à vontade.
COLORS = {
    "primary":    "#2563EB",   # Azul principal
    "secondary":  "#7C3AED",   # Roxo
    "success":    "#059669",   # Verde
    "warning":    "#D97706",   # Laranja
    "danger":     "#DC2626",   # Vermelho
    "neutral":    "#64748B",   # Cinza
    "background": "#0F172A",   # Fundo escuro do painel
    "surface":    "#1E293B",   # Cartões/painéis
    "surface2":   "#263548",   # Fundo de inputs/filtros
    "text":       "#F1F5F9",   # Texto claro
}

# Sequência de cores para gráficos com múltiplas categorias
COLOR_SEQUENCE = [
    "#2563EB", "#7C3AED", "#059669", "#D97706",
    "#DC2626", "#0891B2", "#DB2777", "#65A30D",
]

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA CENTRAL DE RELATÓRIOS
# -----------------------------------------------------------------------------
RELATORIOS_CONFIG = {
    # SETOR: VENDAS
    "vendas_por_produto": {
        "titulo": "Vendas por Produto",
        "setor": "Vendas",
        "sql": "SELECT FIRST 10 PRODUTO, SUM(VALOR) AS TOTAL FROM NOTAS GROUP BY PRODUTO ORDER BY 2 DESC",
        "tipo_grafico": "bar"
    },
    
    # SETOR: ESTOQUE
    "produto_sem_giro": {
        "titulo": "Produto sem Giro",
        "setor": "Estoque",
        "sql": """
            select
            produto.codpro,
            Produto.DesPro,
            grupo.descricao as Grupo,
            subgrupo.descricao as subgrupo, 
            estoque.estoque,
            estoque.venda as Preco_Venda,
            estoque.custo as Preco_Custo
            from estoque
            inner join produto on Estoque.codpro = produto.codpro
            inner join grupo on produto.grupo = grupo.codigo
            inner join subgrupo on produto.subgrupo = subgrupo.subgrupo and grupo.codigo = subgrupo.grupo
            where estoque.estoque > 0
            and produto.codpro not in(select sainota1.codpro from sainota
                                      inner join sainota1 on sainota.id = sainota1.id
                                      and sainota.cod_emp = sainota1.cod_emp
                                      inner join tipvenda on sainota.tipvenda = tipvenda.codigo
                                      where sainota.dat_che >= DATEADD( :DIAS DAY TO current_date )
                                      and sainota.cod_emp = :codemp
                                      and sainota.fechado ='S'
                                      and Sainota.NotCan = 'N'
                                      and TipVenda.EntraMovimento = 'S')
            order by 3,1
        """,
        "tipo_grafico": "multi",
        "parametros": {"DIAS": -90, "codemp": "001"}
    },
    "estoque_baixo": {
        "titulo": "Itens com Estoque Baixo",
        "setor": "Estoque",
        "sql": "SELECT DESCRIÇÃO, ESTOQUE_ATUAL FROM PRODUTOS WHERE ESTOQUE_ATUAL < ESTOQUE_MINIMO",
        "tipo_grafico": "bar"
    },

    # SETOR: FINANCEIRO
    "contas_pagar": {
        "titulo": "Contas a Pagar (Próximos 30 dias)",
        "setor": "Financeiro",
        "sql": "SELECT VENCIMENTO, SUM(VALOR) AS TOTAL FROM TITULOS WHERE TIPO = 'P' GROUP BY VENCIMENTO",
        "tipo_grafico": "line"
    },

    # SETOR: CAIXA E BANCO
    "movimento_caixas": {
        "titulo": "Movimento de Caixas",
        "setor": "Caixa e Banco",
        "sql": "SQL_MOVIMENTO_CAIXAS",
        "tipo_grafico": "multi",
        "parametros": ["pdatai", "pdataf"]
    },
    "fluxo_caixa": {
        "titulo": "Saldo por Conta",
        "setor": "Caixa e Banco",
        "sql": "SELECT NOME_CONTA, SALDO_ATUAL FROM CONTAS_BANCARIAS",
        "tipo_grafico": "bar"
    }
}
