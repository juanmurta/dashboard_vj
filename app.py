# =============================================================================
# app.py — Ponto de entrada principal da aplicação Dash
# =============================================================================
# Este arquivo:
#   1. Cria e configura a aplicação Dash
#   2. Define o layout da página (estrutura HTML)
#   3. Define os callbacks (reatividade: o que acontece quando o usuário age)
#
# Execute com:  python app.py
# Acesse em:    http://localhost:8050
# =============================================================================

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, dash_table
import pandas as pd

# Módulos do projeto
from config import APP_CONFIG, COLORS
from components.layout import (
    criar_filtros,
    criar_card_kpi,
    criar_linha_graficos,
    criar_tabela_container,
)
from reports.notas_saida import (
    buscar_notas,
    calcular_kpis,
    grafico_faturamento_diario,
    grafico_por_vendedor,
    grafico_por_classificacao,
    grafico_por_forma_pagamento,
    grafico_por_cidade,
    grafico_canceladas_vs_ativas,
)

# =============================================================================
# INICIALIZAÇÃO DO APP
# =============================================================================

app = dash.Dash(
    __name__,
    # DBC (Dash Bootstrap Components): grid responsivo, cards, botões, etc.
    # DARKLY = tema escuro do Bootstrap, compatível com nosso CSS personalizado
    external_stylesheets=[dbc.themes.DARKLY],
    title=APP_CONFIG["title"],

    # Suprime exceções de callback para IDs que ainda não existem no layout
    # (útil quando usamos layouts dinâmicos)
    suppress_callback_exceptions=True,
)

# Expõe o servidor Flask subjacente (necessário para deploy em produção)
server = app.server

# =============================================================================
# LAYOUT DA APLICAÇÃO
# =============================================================================
# O layout é a estrutura HTML da página.
# dbc.Container → dbc.Row → dbc.Col segue o grid Bootstrap de 12 colunas.
# =============================================================================

app.layout = html.Div([

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    html.Div([
        html.Div("🥗", style={"fontSize": "36px"}),
        html.Div([
            html.H1("Vieira JR · Painel Comercial"),
            html.P("Análise de Notas de Saída · Firebird 5.0"),
        ]),
        html.Span("DEMO", className="header-badge"),
    ], className="app-header"),

    # -------------------------------------------------------------------------
    # CONTEÚDO PRINCIPAL
    # -------------------------------------------------------------------------
    dbc.Container([

        # --- Painel de Filtros ---
        criar_filtros(),

        # --- Store: armazena os dados da última consulta em memória ---
        # O dcc.Store é invisível — serve para compartilhar dados entre callbacks
        # sem precisar consultar o banco duas vezes.
        dcc.Store(id="store-dados", storage_type="memory"),

        # --- Alerta de status (exibido após consulta) ---
        html.Div(id="alerta-status"),

        # --- Cards de KPI (linha de indicadores) ---
        html.Div(id="kpi-container", className="mb-3"),

        # --- Linha 1: Faturamento Diário + Vendedores ---
        criar_linha_graficos(
            "grafico-faturamento-diario",
            "grafico-por-vendedor",
        ),

        # --- Linha 2: Classificação de Venda + Forma de Pagamento ---
        criar_linha_graficos(
            "grafico-classificacao",
            "grafico-forma-pagamento",
        ),

        # --- Linha 3: Cidades (largura total) + Canceladas vs Ativas ---
        criar_linha_graficos(
            "grafico-cidades",
            "grafico-canceladas",
        ),

        # --- Tabela de dados detalhados ---
        criar_tabela_container(),

    ], fluid=True, style={"padding": "0 24px 40px"}),

], style={"minHeight": "100vh", "backgroundColor": COLORS["background"]})


# =============================================================================
# CALLBACKS — A reatividade do Dash
# =============================================================================
# Um callback é uma função Python que:
#   - É chamada automaticamente quando um Input muda
#   - Atualiza um ou mais Outputs
#
# Fluxo desta aplicação:
#   [Usuário clica em "Consultar"]
#       → callback_consultar_dados() busca no banco e salva no Store
#       → callback_atualizar_dashboard() lê do Store e atualiza todos os visuais
#
# Separar em dois callbacks evita consultas duplicadas ao banco.
# =============================================================================


# -----------------------------------------------------------------------------
# CALLBACK 1: Consultar banco e guardar dados no Store
# -----------------------------------------------------------------------------
@app.callback(
    Output("store-dados", "data"),          # Salva o JSON no Store
    Output("alerta-status", "children"),    # Exibe mensagem de sucesso/erro
    Input("btn-consultar", "n_clicks"),     # Disparado pelo clique no botão
    State("input-coligada", "value"),       # Lê os filtros (State = não dispara)
    State("input-data-ini", "value"),   # dbc.Input usa "value", não "date"
    State("input-data-fim", "value"),   # dbc.Input usa "value", não "date"
    prevent_initial_call=True,              # Não executa ao carregar a página
)
def consultar_dados(n_clicks, coligada, data_ini, data_fim):
    """
    Busca os dados no Firebird e armazena como JSON no dcc.Store.
    Retorna também uma mensagem de status para o usuário.
    """
    # Validação básica dos filtros
    if not coligada or not data_ini or not data_fim:
        return dash.no_update, dbc.Alert(
            "⚠️ Preencha todos os filtros antes de consultar.",
            color="warning", dismissable=True,
        )

    # Passa coligada como string — o banco armazena cod_emp como CHAR/VARCHAR
    # com zeros à esquerda (ex: '001', '002'). Converter para int quebraria a comparação.
    df = buscar_notas(str(coligada).strip(), data_ini, data_fim)

    if df.empty:
        return None, dbc.Alert(
            f"ℹ️ Nenhuma nota encontrada para o período {data_ini} a {data_fim}.",
            color="info", dismissable=True,
        )

    # Converte datas para string antes de serializar para JSON
    # (JSON não suporta datetime nativamente)
    df["DAT_EMI"] = df["DAT_EMI"].astype(str)
    df["DAT_CHE"] = df["DAT_CHE"].astype(str)

    qtd = len(df)
    alerta = dbc.Alert(
        f"✅ Consulta concluída: {qtd} nota(s) encontrada(s) no período.",
        color="success", dismissable=True, duration=4000,
    )

    # to_json() serializa o DataFrame para string JSON armazenada no Store
    return df.to_json(date_format="iso", orient="split"), alerta


# -----------------------------------------------------------------------------
# CALLBACK 2: Atualizar dashboard completo com os dados do Store
# -----------------------------------------------------------------------------
@app.callback(
    # KPIs
    Output("kpi-container", "children"),

    # Gráficos
    Output("grafico-faturamento-diario", "figure"),
    Output("grafico-por-vendedor", "figure"),
    Output("grafico-classificacao", "figure"),
    Output("grafico-forma-pagamento", "figure"),
    Output("grafico-cidades", "figure"),
    Output("grafico-canceladas", "figure"),

    # Tabela
    Output("tabela-notas", "children"),

    Input("store-dados", "data"),       # Disparado quando o Store muda
)
def atualizar_dashboard(dados_json):
    """
    Lê os dados do Store e atualiza todos os componentes visuais.
    É chamado automaticamente sempre que o Store é atualizado pelo Callback 1.
    """
    import traceback
    try:
        # Estado inicial: Store vazio (antes da primeira consulta)
        if dados_json is None:
            fig_vazia = _figura_placeholder()
            kpis_vazios = _kpis_placeholder()
            tabela_vazia = html.P(
                "Preencha os filtros e clique em Consultar para ver os dados.",
                style={"color": COLORS["neutral"], "textAlign": "center", "padding": "20px"},
            )
            return (
                kpis_vazios,
                fig_vazia, fig_vazia, fig_vazia,
                fig_vazia, fig_vazia, fig_vazia,
                tabela_vazia,
            )

        # Desserializa o JSON de volta para DataFrame
        import io
        df = pd.read_json(io.StringIO(dados_json), orient="split")

        # Reconverte datas (ficaram como string no JSON)
        df["DAT_EMI"] = pd.to_datetime(df["DAT_EMI"], errors="coerce")
        df["DAT_CHE"] = pd.to_datetime(df["DAT_CHE"], errors="coerce")

        # Recria colunas derivadas (se perdidas na serialização)
        if "MES_ANO" not in df.columns:
            # Proteção contra NaT no dt.to_period
            df["MES_ANO"] = df["DAT_EMI"].apply(lambda x: str(x.to_period("M")) if pd.notnull(x) else "N/A")

        if "STATUS_CANCEL" not in df.columns:
            df["STATUS_CANCEL"] = df["CANCELADO"].apply(
                lambda x: "Cancelada" if str(x).strip().upper() == "S" else "Ativa"
            )

        # --- KPIs ---
        kpis = calcular_kpis(df)
        
        def formatar_moeda(valor):
            try:
                v = float(valor) if valor is not None else 0.0
                return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return "R$ 0,00"

        kpi_row = dbc.Row([
            dbc.Col(criar_card_kpi("Total de Notas",    str(kpis.get("total_notas", 0)),
                                   "🧾", COLORS["primary"]),  xs=12, sm=6, lg=2),
            dbc.Col(criar_card_kpi("Faturamento",
                                   formatar_moeda(kpis.get("valor_total", 0)),
                                   "💰", COLORS["success"]),  xs=12, sm=6, lg=2),
            dbc.Col(criar_card_kpi("Ticket Médio",
                                   formatar_moeda(kpis.get("ticket_medio", 0)),
                                   "🎯", COLORS["warning"]),  xs=12, sm=6, lg=2),
            dbc.Col(criar_card_kpi("Notas Ativas",      str(kpis.get("notas_ativas", 0)),
                                   "✅", COLORS["success"]),  xs=12, sm=6, lg=2),
            dbc.Col(criar_card_kpi("Canceladas",         str(kpis.get("notas_canceladas", 0)),
                                   "❌", COLORS["danger"]),   xs=12, sm=6, lg=2),
            dbc.Col(criar_card_kpi("Clientes Únicos",    str(kpis.get("clientes_unicos", 0)),
                                   "👤", COLORS["secondary"]),xs=12, sm=6, lg=2),
        ], className="g-3 mb-3")

        # --- Gráficos ---
        fig_diario     = grafico_faturamento_diario(df)
        fig_vendedor   = grafico_por_vendedor(df)
        fig_classif    = grafico_por_classificacao(df)
        fig_pagamento  = grafico_por_forma_pagamento(df)
        fig_cidade     = grafico_por_cidade(df)
        fig_canceladas = grafico_canceladas_vs_ativas(df)

        # --- Tabela de dados ---
        # Seleciona e formata as colunas para exibição
        colunas_tabela = ["NOTA", "DAT_EMI", "NOMECLI", "CIDADE", "NOMFUN",
                          "CLASSIFICACAO", "FORMAPAG", "VALOR", "STATUS_CANCEL"]
        colunas_tabela = [c for c in colunas_tabela if c in df.columns]

        df_tabela = df[colunas_tabela].copy()
        df_tabela["DAT_EMI"] = df_tabela["DAT_EMI"].dt.strftime("%d/%m/%Y")
        df_tabela["VALOR"]   = df_tabela["VALOR"].apply(formatar_moeda)

        tabela = dash_table.DataTable(
            data=df_tabela.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_tabela.columns],
            page_size=15,                       # Linhas por página
            sort_action="native",               # Ordenação clicando no cabeçalho
            filter_action="native",             # Filtro por coluna
            style_table={"overflowX": "auto"},  # Scroll horizontal no mobile
            style_cell={"textAlign": "left", "padding": "8px 12px"},
            style_header={"fontWeight": "bold"},
        )

        return (
            kpi_row,
            fig_diario, fig_vendedor, fig_classif,
            fig_pagamento, fig_cidade, fig_canceladas,
            tabela,
        )
    except Exception as e:
        print(f"❌ ERRO NO CALLBACK: {str(e)}")
        traceback.print_exc()
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# -----------------------------------------------------------------------------
# CALLBACK 3: Exportar tabela como CSV
# -----------------------------------------------------------------------------
@app.callback(
    Output("download-csv", "data"),
    Input("btn-export", "n_clicks"),
    State("store-dados", "data"),
    prevent_initial_call=True,
)
def exportar_csv(n_clicks, dados_json):
    """Gera download do CSV com os dados atualmente exibidos."""
    if dados_json is None:
        return dash.no_update

    import io
    df = pd.read_json(io.StringIO(dados_json), orient="split")
    return dcc.send_data_frame(df.to_csv, "notas_saida.csv", index=False, sep=";")


# =============================================================================
# FUNÇÕES AUXILIARES LOCAIS
# =============================================================================

def _figura_placeholder():
    """Gráfico vazio exibido antes da primeira consulta."""
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_annotation(
        text="Consulte os dados usando os filtros acima",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=13, color=COLORS["neutral"]),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def _kpis_placeholder():
    """Row de KPIs vazia exibida antes da primeira consulta."""
    return dbc.Row([
        dbc.Col(criar_card_kpi(label, "—", icone, COLORS["neutral"]), xs=12, sm=6, lg=2)
        for label, icone in [
            ("Total de Notas", "🧾"), ("Faturamento", "💰"), ("Ticket Médio", "🎯"),
            ("Notas Ativas", "✅"),   ("Canceladas", "❌"),  ("Clientes Únicos", "👤"),
        ]
    ], className="g-3 mb-3")


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print(f"  🚀 {APP_CONFIG['title']}")
    print("="*60)
    print(f"  Acesse: http://localhost:{APP_CONFIG['port']}")
    print(f"  Na rede: http://SEU_IP:{APP_CONFIG['port']}")
    print("="*60 + "\n")

    app.run(
        debug=APP_CONFIG["debug"],
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"],
    )
