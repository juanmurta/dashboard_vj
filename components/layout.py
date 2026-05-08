# =============================================================================
# components/layout.py — Componentes visuais reutilizáveis do Dash
# =============================================================================
# Funções que retornam blocos de HTML/Dash prontos para usar no app.py.
# Separar o layout aqui mantém o app.py limpo e focado na lógica.
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from config import COLORS
from datetime import date, timedelta


def criar_card_kpi(titulo: str, valor: str, icone: str, cor: str = None) -> dbc.Card:
    """
    Cria um card de KPI (indicador) para o topo do dashboard.

    Args:
        titulo (str): Rótulo do indicador. Ex: "Total de Notas"
        valor  (str): Valor formatado. Ex: "R$ 125.430,00"
        icone  (str): Emoji ou ícone. Ex: "📦"
        cor    (str): Cor da borda esquerda (hex). Padrão: azul primário.

    Returns:
        dbc.Card: Componente Dash pronto para ser inserido no layout.
    """
    cor = cor or COLORS["primary"]

    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icone, style={"fontSize": "28px"}),
                html.Div([
                    html.P(titulo, className="kpi-label"),
                    html.H4(valor, className="kpi-value"),
                ]),
            ], className="kpi-inner"),
        ]),
        className="kpi-card",
        style={"borderLeft": f"4px solid {cor}"},
    )


def criar_filtros() -> dbc.Card:
    """
    Painel de filtros: coligada, data inicial e data final.
    O usuário preenche esses campos e clica em "Consultar".

    Returns:
        dbc.Card: Card com os filtros e botão de consulta.
    """
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)

    return dbc.Card(
        dbc.CardBody([
            html.H5("🔍 Filtros", className="section-title"),
            dbc.Row([
                # Campo: Coligada
                dbc.Col([
                    dbc.Label("Coligada (Empresa)", html_for="input-coligada"),
                    dbc.Input(
                        id="input-coligada",
                        type="text",
                        value="001",        # Valor padrão — use o cod_emp exato do banco
                        placeholder="Ex: 001",
                        className="dash-input",
                    ),
                ], xs=12, sm=4, md=2),

                # Campo: Data Inicial
                # Usamos dbc.Input type="date" ao invés do dcc.DatePickerSingle
                # porque o DatePickerSingle usa um componente React interno que
                # ignora CSS externo e exibe texto branco sobre fundo branco em
                # temas escuros. O input nativo HTML respeita 100% o CSS.
                dbc.Col([
                    dbc.Label("Data Inicial", html_for="input-data-ini"),
                    dbc.Input(
                        id="input-data-ini",
                        type="date",
                        value=primeiro_dia_mes.strftime("%Y-%m-%d"),
                        className="date-input",
                    ),
                ], xs=12, sm=4, md=3),

                # Campo: Data Final
                dbc.Col([
                    dbc.Label("Data Final", html_for="input-data-fim"),
                    dbc.Input(
                        id="input-data-fim",
                        type="date",
                        value=hoje.strftime("%Y-%m-%d"),
                        className="date-input",
                    ),
                ], xs=12, sm=4, md=3),

                # Botão Consultar
                dbc.Col([
                    dbc.Label("\u00a0"),   # Espaçador para alinhar com os inputs
                    dbc.Button(
                        "⚡ Consultar",
                        id="btn-consultar",
                        color="primary",
                        className="btn-consultar w-100",
                        n_clicks=0,
                    ),
                ], xs=12, sm=12, md=2),

                # Indicador de carregamento (aparece enquanto busca dados)
                dbc.Col([
                    dbc.Label("\u00a0"),
                    html.Div(
                        dbc.Spinner(size="sm", color="primary"),
                        id="loading-indicator",
                        style={"display": "none", "paddingTop": "8px"},
                    ),
                ], xs=12, sm=12, md=2),
            ], align="end", className="g-3"),
        ]),
        className="filter-card",
    )


def criar_linha_graficos(grafico_id_esq: str, grafico_id_dir: str,
                          titulo_esq: str = "", titulo_dir: str = "") -> dbc.Row:
    """
    Cria uma linha com dois gráficos lado a lado (layout responsivo).

    Args:
        grafico_id_esq (str): ID do dcc.Graph da esquerda
        grafico_id_dir (str): ID do dcc.Graph da direita
        titulo_esq     (str): Título opcional para o card esquerdo
        titulo_dir     (str): Título opcional para o card direito

    Returns:
        dbc.Row com dois cards de gráfico.
    """
    def card_grafico(graph_id, titulo):
        corpo = []
        if titulo:
            corpo.append(html.H6(titulo, className="chart-title"))
        corpo.append(
            dcc.Graph(
                id=graph_id,
                config={
                    "displayModeBar": True,       # Barra de ferramentas do Plotly
                    "modeBarButtonsToRemove": [    # Remove botões desnecessários
                        "lasso2d", "select2d", "autoScale2d"
                    ],
                    "displaylogo": False,          # Remove logo do Plotly
                    "toImageButtonOptions": {      # Configuração do botão "salvar imagem"
                        "format": "png",
                        "filename": graph_id,
                        "scale": 2,                # Alta resolução
                    },
                },
                style={"height": "380px"},
            )
        )
        return dbc.Card(dbc.CardBody(corpo), className="chart-card")

    return dbc.Row([
        dbc.Col(card_grafico(grafico_id_esq, titulo_esq), xs=12, lg=6),
        dbc.Col(card_grafico(grafico_id_dir, titulo_dir), xs=12, lg=6),
    ], className="g-3 mb-3")


def criar_tabela_container() -> html.Div:
    """
    Container para a tabela de dados brutos no final da página.
    A tabela em si é gerada dinamicamente no callback.
    """
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H5("📋 Dados Detalhados", className="section-title"),
                    dbc.Button(
                        "⬇ Exportar CSV",
                        id="btn-export",
                        color="secondary",
                        size="sm",
                        outline=True,
                    ),
                ], className="table-header"),
                html.Div(id="tabela-notas"),   # Preenchido pelo callback
                dcc.Download(id="download-csv"),
            ])
        ], className="chart-card"),
    ], className="mb-4")
