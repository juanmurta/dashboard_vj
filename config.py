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
    "host": "192.168.25.73",

    # Porta padrão do Firebird (3050). Altere se usar porta customizada.
    "port": 3050,

    # Caminho COMPLETO do arquivo .FDB no servidor remoto
    "database": r"D:\Makemoney\Dados\Renutri\VISAWORK.FDB",

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
    "title": "Renutri — Painel de Relatórios",

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
    "text":       "#F1F5F9",   # Texto claro
}

# Sequência de cores para gráficos com múltiplas categorias
COLOR_SEQUENCE = [
    "#2563EB", "#7C3AED", "#059669", "#D97706",
    "#DC2626", "#0891B2", "#DB2777", "#65A30D",
]