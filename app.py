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
from config import APP_CONFIG, COLORS, RELATORIOS_CONFIG
from database.connection import executar_query
from components.layout import (
    criar_navbar,
    criar_sidebar_relatorios,
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
from reports.produtos_sem_giro import (
    buscar_produtos_sem_giro,
    calcular_kpis_sem_giro,
    grafico_por_grupo,
)
from reports.movimento_caixas import (
    buscar_movimento_caixas,
    calcular_kpis_movimento,
    grafico_entradas_saidas_pizza,
    grafico_movimentacao_diaria,
    grafico_por_caixa_banco,
    grafico_saldo_acumulado,
)
from reports.posicao_estoque_vendas import (
    buscar_posicao_estoque_vendas,
    calcular_kpis_posicao,
    grafico_custo_por_grupo,
    grafico_vendas_vs_estoque,
)
from reports.inadimplencia import (
    buscar_inadimplencia,
    calcular_kpis_inadimplencia,
    grafico_por_vendedor as grafico_inad_vendedor,
    grafico_por_cidade as grafico_inad_cidade,
    grafico_faixas_atraso,
    grafico_por_cliente as grafico_inad_cliente,
)
from reports.faturamento_por_estoque import (
    buscar_faturamento_por_estoque,
    calcular_kpis_faturamento,
    grafico_faturamento_por_grupo,
    grafico_vendedor_comissao,
    grafico_faturamento_temporal,
    grafico_por_tipo_documento,
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
# LAYOUTS DAS PÁGINAS
# =============================================================================

def layout_comercial():
    """Retorna o layout da página do Painel Comercial (Dashboard Geral)"""
    fig_vazia = _figura_placeholder()
    kpis_vazios = _kpis_placeholder()
    
    return html.Div([
        # --- HEADER (Agora dentro do layout da página ou removido se usar Navbar) ---
        html.Div([
            html.Div("🥗", style={"fontSize": "36px"}),
            html.Div([
                html.H1("Vieira JR · Painel Comercial"),
                html.P("Análise de Notas de Saída · Firebird 5.0"),
            ]),
            html.Span("DEMO", className="header-badge"),
        ], className="app-header"),

        dbc.Container([
            # --- Painel de Filtros ---
            criar_filtros(),

            # --- Alerta de status (exibido após consulta) ---
            html.Div(id="alerta-status"),

            # --- Cards de KPI (linha de indicadores) ---
            html.Div(id="kpi-container", children=kpis_vazios, className="mb-3"),

            # --- Linha 1: Faturamento Diário + Vendedores ---
            criar_linha_graficos(
                "grafico-faturamento-diario",
                "grafico-por-vendedor",
                fig_padrao=fig_vazia
            ),

            # --- Linha 2: Classificação de Venda + Forma de Pagamento ---
            criar_linha_graficos(
                "grafico-classificacao",
                "grafico-forma-pagamento",
                fig_padrao=fig_vazia
            ),

            # --- Linha 3: Cidades (largura total) + Canceladas vs Ativas ---
            criar_linha_graficos(
                "grafico-cidades",
                "grafico-canceladas",
                fig_padrao=fig_vazia
            ),

            # --- Tabela de dados detalhados ---
            criar_tabela_container(),

        ], fluid=True, style={"padding": "0 24px 40px"}),
    ])


def layout_relatorios():
    """Retorna o layout da página Central de Relatórios"""
    fig_vazia = _figura_placeholder()
    kpis_vazios = _kpis_placeholder()
    
    return html.Div([
        html.Div([
            html.Div("📑", style={"fontSize": "36px"}),
            html.Div([
                html.H1("Vieira JR · Central de Relatórios"),
                html.P("Relatórios Setoriais Dinâmicos"),
            ]),
        ], className="app-header"),

        dbc.Container([
            # --- Painel de Filtros Reutilizado ---
            criar_filtros(),

            # --- Alerta de status ---
            html.Div(id="alerta-status"),

            dbc.Row([
                # Coluna Esquerda: Menu de Relatórios
                dbc.Col([
                    criar_sidebar_relatorios(RELATORIOS_CONFIG)
                ], xs=12, md=3, lg=2),

                # Coluna Direita: Exibição do Relatório
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Visualização do Relatório", id="relatorio-titulo")),
                        dbc.CardBody([
                            # KPIs Dinâmicos do Relatório
                            html.Div(id="kpi-container-relatorios", children=kpis_vazios, className="mb-3"),

                            html.Div(id="relatorio-conteudo", children=[
                                html.P("Selecione um relatório no menu lateral para visualizar os dados.",
                                       className="text-muted text-center", style={"padding": "50px"})
                            ])
                        ])
                    ], className="chart-card")
                ], xs=12, md=9, lg=10),
            ], className="g-4")
        ], fluid=True, style={"padding": "0 24px 40px"}),
    ])


# =============================================================================
# LAYOUT PRINCIPAL (FRAMEWORK)
# =============================================================================
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    # --- Stores globais para persistência entre páginas ---
    dcc.Store(id="store-dados", storage_type="memory"),
    dcc.Store(id="store-dados-relatorios", storage_type="memory"),
    dcc.Store(id="relatorio-ativo", data="comercial"),

    criar_navbar(),
    html.Div(id="conteudo-pagina"),
], style={"minHeight": "100vh", "backgroundColor": COLORS["background"]})


# =============================================================================
# CALLBACK DE ROTEAMENTO
# =============================================================================

@app.callback(
    Output("conteudo-pagina", "children"),
    Output("relatorio-ativo", "data"),
    Input("url", "pathname"),
    State("relatorio-ativo", "data"),
)
def display_page(pathname, rel_atual):
    if pathname == "/relatorios":
        # Se já estiver em algum relatório, não reseta para None
        novo_rel = rel_atual if rel_atual != "comercial" else None
        return layout_relatorios(), novo_rel
    else:
        # Default: Painel Comercial
        return layout_comercial(), "comercial"


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
# CALLBACK 0: Controlar visibilidade dos filtros baseada no relatório
# -----------------------------------------------------------------------------
@app.callback(
    Output("container-coligada", "style"),
    Output("container-data-ini", "style"),
    Output("container-data-fim", "style"),
    Output("container-dias", "style"),
    Input("relatorio-ativo", "data"),
)
def alternar_filtros(rel_id):
    if rel_id == "produto_sem_giro":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "block"}
    elif rel_id == "posicao_estoque_vendas":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "none"}
    elif rel_id == "movimento_caixas":
        # Esconde coligada conforme pedido, mas mantém datas
        return {"display": "none"}, {"display": "block"}, {"display": "block"}, {"display": "none"}
    elif rel_id in ["comercial", "faturamento_por_estoque"]:
        return {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "none"}
    elif rel_id is None:
        # Quando entra na página de relatórios sem selecionar nenhum
        return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}
    else:
        # Outros relatórios podem precisar de data ou nada
        return {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "none"}

# -----------------------------------------------------------------------------
# CALLBACK 1: Consultar banco e guardar dados no Store
# -----------------------------------------------------------------------------
@app.callback(
    Output("store-dados", "data"),          # Para layout comercial
    Output("store-dados-relatorios", "data"), # Para layout relatórios
    Output("alerta-status", "children"),
    Output("input-coligada", "value", allow_duplicate=True),
    Output("input-data-ini", "value"),
    Output("input-data-fim", "value"),
    Output("input-dias", "value"),
    Input("btn-consultar", "n_clicks"),     
    State("relatorio-ativo", "data"),
    State("input-coligada", "value"),       
    State("input-data-ini", "value"),   
    State("input-data-fim", "value"),   
    State("input-dias", "value"),
    prevent_initial_call=True,              
)
def consultar_dados(n_clicks, rel_id, coligada, data_ini, data_fim, dias):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Valores para manter os inputs em caso de erro de validação
    manter_inputs = [dash.no_update, dash.no_update, dash.no_update, dash.no_update]

    coligadas = coligada if isinstance(coligada, (list, tuple, set)) else [coligada] if coligada else []

    if not coligadas and rel_id != "movimento_caixas":
        alerta = dbc.Alert("Selecione ao menos uma coligada", color="warning")
        return dash.no_update, dash.no_update, alerta, *manter_inputs

    if rel_id == "comercial" or rel_id is None:
        df = buscar_notas(coligadas, data_ini, data_fim)
        if not df.empty:
            df["DAT_EMI"] = df["DAT_EMI"].astype(str)
            df["DAT_CHE"] = df["DAT_CHE"].astype(str)
        
        alerta = dbc.Alert(f"✅ {len(df)} notas encontradas", color="success", duration=4000)
        return df.to_json(date_format="iso", orient="split"), dash.no_update, alerta, *manter_inputs

    elif rel_id == "movimento_caixas":
        df = buscar_movimento_caixas(data_ini, data_fim)
        if not df.empty:
            # Garante colunas em maiúsculas
            df.columns = [c.upper() for c in df.columns]
            if "DATAMOV" in df.columns:
                df["DATAMOV"] = df["DATAMOV"].astype(str)
        alerta = dbc.Alert(f"✅ {len(df)} lançamentos encontrados", color="success", duration=4000)
        return dash.no_update, df.to_json(date_format="iso", orient="split"), alerta, *manter_inputs

    elif rel_id == "produto_sem_giro":
        try:
            dias_val = int(dias) if dias else 90
        except (ValueError, TypeError):
            dias_val = 90
        
        df = buscar_produtos_sem_giro(coligadas, dias_val)
        alerta = dbc.Alert(f"✅ {len(df)} produtos encontrados", color="success", duration=4000)
        return dash.no_update, df.to_json(date_format="iso", orient="split"), alerta, *manter_inputs
    
    elif rel_id == "posicao_estoque_vendas":
        df = buscar_posicao_estoque_vendas(coligadas)
        alerta = dbc.Alert(f"✅ {len(df)} itens em estoque encontrados", color="success", duration=4000)
        return dash.no_update, df.to_json(date_format="iso", orient="split"), alerta, *manter_inputs

    elif rel_id == "inadimplencia_periodo":
        df = buscar_inadimplencia(coligadas, data_ini, data_fim)
        alerta = dbc.Alert(f"✅ {len(df)} títulos em atraso encontrados", color="success", duration=4000)
        return dash.no_update, df.to_json(date_format="iso", orient="split"), alerta, *manter_inputs

    elif rel_id == "faturamento_por_estoque":
        df = buscar_faturamento_por_estoque(coligadas, data_ini, data_fim)
        alerta = dbc.Alert(f"✅ {len(df)} registros de faturamento encontrados", color="success", duration=4000)
        return dash.no_update, df.to_json(date_format="iso", orient="split"), alerta, *manter_inputs

    # Se cair aqui, pelo menos retorna dash.no_update corretamente para todos os outputs
    return dash.no_update, dash.no_update, dash.no_update, *manter_inputs


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
    prevent_initial_call=True,
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
            filter_options={
                "placeholder_text": "Use '=' para busca exata (ex: =417)",
                "case": "insensitive"
            },
            # Configuração de filtragem
            filter_query="",
            # Customização do comportamento de filtragem para colunas específicas
            derived_filter_query_structure=None, 
            tooltip_header={
                "CODPRO": "Para busca exata, use '='. Ex: =417",
                "NOTA": "Para busca exata, use '='."
            },
            tooltip_delay=0,
            tooltip_duration=None,
            style_table={"overflowX": "auto"},  # Scroll horizontal no mobile
            style_cell={
                "textAlign": "left",
                "padding": "8px 12px",
                "backgroundColor": COLORS["surface"],
                "color": COLORS["text"],
                "fontFamily": "Inter, sans-serif",
            },
            style_header={
                "backgroundColor": COLORS["surface2"],
                "fontWeight": "bold",
                "color": COLORS["text"],
                "border": f"1px solid {COLORS['neutral']}33",
                "textDecoration": "underline",
                "textDecorationStyle": "dotted",
                "cursor": "help",
            },
            style_filter={
                "backgroundColor": COLORS["surface2"],
                "color": COLORS["text"],
            },
            style_data={
                "border": f"1px solid {COLORS['neutral']}33",
            },
            # Estilo condicional para quando o usuário clica/seleciona uma célula
            style_data_conditional=[
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(37, 99, 235, 0.2)",
                    "border": f"1px solid {COLORS['primary']}",
                }
            ],
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


# -----------------------------------------------------------------------------
# CALLBACK 4: Selecionar Relatório e Atualizar UI
# -----------------------------------------------------------------------------
@app.callback(
    Output("relatorio-titulo", "children"),
    Output("relatorio-ativo", "data", allow_duplicate=True),
    Input({"type": "btn-relatorio", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def selecionar_relatorio(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # Se todos n_clicks forem None ou 0, não faz nada
    if not any(n_clicks):
        return dash.no_update, dash.no_update

    rel_id = ctx.triggered_id["index"]
    config = RELATORIOS_CONFIG.get(rel_id)
    return config["titulo"], rel_id

# -----------------------------------------------------------------------------
# CALLBACK 5: Atualizar Relatório com Dados do Store
# -----------------------------------------------------------------------------
@app.callback(
    Output("kpi-container-relatorios", "children"),
    Output("relatorio-conteudo", "children"),
    Input("store-dados-relatorios", "data"),
    State("relatorio-ativo", "data"),
    prevent_initial_call=True,
)
def atualizar_relatorio(dados_json, rel_id):
    import traceback
    try:
        if not dados_json or not rel_id:
            return dash.no_update, dash.no_update

        import io
        df = pd.read_json(io.StringIO(dados_json), orient="split")

        if rel_id == "produto_sem_giro":
            kpis = calcular_kpis_sem_giro(df)
            
            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            kpi_row = dbc.Row([
                dbc.Col(criar_card_kpi("Itens sem Giro", str(kpis["total_itens"]), "📦", COLORS["primary"]), md=3),
                dbc.Col(criar_card_kpi("Valor Parado", formatar_moeda(kpis["valor_parado"]), "💰", COLORS["danger"]), md=3),
                dbc.Col(criar_card_kpi("Estoque Total", str(kpis["estoque_total"]), "📊", COLORS["warning"]), md=3),
                dbc.Col(criar_card_kpi("Grupos Afetados", str(kpis["grupos_afetados"]), "📁", COLORS["secondary"]), md=3),
            ], className="g-3 mb-4")

            fig = grafico_por_grupo(df)
            
            tabela = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "backgroundColor": COLORS["surface"], "color": COLORS["text"]},
                style_header={"backgroundColor": COLORS["surface2"], "fontWeight": "bold", "color": COLORS["text"]},
            )

            conteudo = [
                html.H5("Valor Parado por Grupo"),
                dcc.Graph(figure=fig),
                html.Hr(),
                html.H5("Detalhamento dos Produtos"),
                tabela
            ]

            return kpi_row, conteudo

        elif rel_id == "posicao_estoque_vendas":
            kpis = calcular_kpis_posicao(df)
            
            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            kpi_row = dbc.Row([
                dbc.Col(criar_card_kpi("Total Produtos", str(kpis["total_produtos"]), "📦", COLORS["primary"]), md=3),
                dbc.Col(criar_card_kpi("Custo Estoque", formatar_moeda(kpis["custo_total_estoque"]), "💰", COLORS["warning"]), md=3),
                dbc.Col(criar_card_kpi("Vendas (180d)", formatar_moeda(kpis["total_vendas_periodo"]), "📊", COLORS["success"]), md=3),
                dbc.Col(criar_card_kpi("Abaixo do Mínimo", str(kpis["itens_abaixo_minimo"]), "⚠️", COLORS["danger"]), md=3),
            ], className="g-3 mb-4")

            fig_pizza = grafico_custo_por_grupo(df)
            fig_barras = grafico_vendas_vs_estoque(df)
            
            tabela = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "backgroundColor": COLORS["surface"], "color": COLORS["text"]},
                style_header={"backgroundColor": COLORS["surface2"], "fontWeight": "bold", "color": COLORS["text"]},
            )

            conteudo = [
                dbc.Row([
                    dbc.Col([html.H5("Custo por Grupo"), dcc.Graph(figure=fig_pizza)], md=4),
                    dbc.Col([html.H5("Top 15 Vendas vs Estoque"), dcc.Graph(figure=fig_barras)], md=8),
                ], className="mb-4"),
                html.Hr(),
                html.H5("Detalhamento da Posição"),
                tabela
            ]

            return kpi_row, conteudo

        elif rel_id == "movimento_caixas":
            # Converte as colunas para maiúsculas para garantir consistência
            df.columns = [c.upper() for c in df.columns]
            
            # Reconverte datas (ficaram como string no JSON)
            if "DATAMOV" in df.columns:
                df["DATAMOV"] = pd.to_datetime(df["DATAMOV"], errors="coerce")
            
            # Recria colunas derivadas se necessário (VALOR_SINAL)
            if "VALOR" in df.columns and "DC" in df.columns:
                df["VALOR_SINAL"] = df.apply(
                    lambda x: x["VALOR"] if x["DC"] == "C" else -x["VALOR"], axis=1
                )

            kpis = calcular_kpis_movimento(df)

            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            kpi_row = dbc.Row([
                dbc.Col(criar_card_kpi("Total Entradas", formatar_moeda(kpis["total_entradas"]), "📈", COLORS["success"]), md=3),
                dbc.Col(criar_card_kpi("Total Saídas", formatar_moeda(kpis["total_saidas"]), "📉", COLORS["danger"]), md=3),
                dbc.Col(criar_card_kpi("Saldo Período", formatar_moeda(kpis["saldo_periodo"]), "⚖️", COLORS["primary"]), md=3),
                dbc.Col(criar_card_kpi("Lançamentos", str(kpis["n_lancamentos"]), "📝", COLORS["secondary"]), md=3),
            ], className="g-3 mb-4")

            fig_pizza = grafico_entradas_saidas_pizza(df)
            fig_diario = grafico_movimentacao_diaria(df)
            fig_origem = grafico_por_caixa_banco(df)
            fig_saldo = grafico_saldo_acumulado(df)

            tabela = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns if c != "VALOR_SINAL"],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "backgroundColor": COLORS["surface"], "color": COLORS["text"]},
                style_header={"backgroundColor": COLORS["surface2"], "fontWeight": "bold", "color": COLORS["text"]},
            )

            conteudo = [
                dbc.Row([
                    dbc.Col([html.H5("Entradas vs Saídas"), dcc.Graph(figure=fig_pizza)], md=4),
                    dbc.Col([html.H5("Saldo Acumulado"), dcc.Graph(figure=fig_saldo)], md=8),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([html.H5("Movimentação Diária"), dcc.Graph(figure=fig_diario)], md=7),
                    dbc.Col([html.H5("Volume por Caixa/Banco"), dcc.Graph(figure=fig_origem)], md=5),
                ], className="mb-4"),
                html.Hr(),
                html.H5("Detalhamento de Lançamentos"),
                tabela
            ]

            return kpi_row, conteudo

        elif rel_id == "inadimplencia_periodo":
            # Garante colunas em maiúsculas
            df.columns = [c.upper() for c in df.columns]

            # Recria colunas derivadas e trata tipos (perdidos no JSON)
            if "VRLCONT" in df.columns:
                df["VRLCONT"] = pd.to_numeric(df["VRLCONT"], errors="coerce").fillna(0)
            if "VALJUR" in df.columns:
                df["VALJUR"] = pd.to_numeric(df["VALJUR"], errors="coerce").fillna(0)
            
            df["VALOR_TOTAL"] = df.get("VRLCONT", 0) + df.get("VALJUR", 0)
            
            if "DIASATRASO" in df.columns:
                df["DIASATRASO"] = pd.to_numeric(df["DIASATRASO"], errors="coerce").fillna(0)

            kpis = calcular_kpis_inadimplencia(df)
            
            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            kpi_row = dbc.Row([
                dbc.Col(criar_card_kpi("Total Inadimplente", formatar_moeda(kpis["valor_total"]), "💰", COLORS["danger"]), md=3),
                dbc.Col(criar_card_kpi("Qtd Títulos", str(kpis["qtd_titulos"]), "📄", COLORS["warning"]), md=3),
                dbc.Col(criar_card_kpi("Média Atraso", f"{kpis['media_atraso']} dias", "⏳", COLORS["primary"]), md=3),
                dbc.Col(criar_card_kpi("Maior Atraso", f"{kpis['maior_atraso']} dias", "⚠️", COLORS["secondary"]), md=3),
            ], className="g-3 mb-4")

            fig_vendedor = grafico_inad_vendedor(df)
            fig_cidade = grafico_inad_cidade(df)
            fig_faixas = grafico_faixas_atraso(df)
            fig_cliente = grafico_inad_cliente(df)

            tabela = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns if c not in ["FAIXA_ATRASO", "VALOR_TOTAL"]],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "backgroundColor": COLORS["surface"], "color": COLORS["text"]},
                style_header={"backgroundColor": COLORS["surface2"], "fontWeight": "bold", "color": COLORS["text"]},
            )

            conteudo = [
                dbc.Row([
                    dbc.Col([html.H5("Inadimplência por Faixa de Atraso"), dcc.Graph(figure=fig_faixas)], md=6),
                    dbc.Col([html.H5("Top 10 Cidades"), dcc.Graph(figure=fig_cidade)], md=6),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([html.H5("Top 10 Clientes que Mais Devem"), dcc.Graph(figure=fig_cliente)], md=6),
                    dbc.Col([html.H5("Top 10 Vendedores"), dcc.Graph(figure=fig_vendedor)], md=6),
                ], className="mb-4"),
                html.Hr(),
                html.H5("Detalhamento de Títulos"),
                tabela
            ]

            return kpi_row, conteudo

        elif rel_id == "faturamento_por_estoque":
            # Converte as colunas de data
            if "DAT_CHE" in df.columns:
                df["DAT_CHE"] = pd.to_datetime(df["DAT_CHE"], errors="coerce")

            kpis = calcular_kpis_faturamento(df)

            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            kpi_row = dbc.Row([
                dbc.Col(criar_card_kpi("Faturamento Total", formatar_moeda(kpis["faturamento_total"]), "💰", COLORS["success"]), md=3),
                dbc.Col(criar_card_kpi("Margem Bruta", formatar_moeda(kpis["margem_bruta"]), "⚖️", COLORS["primary"]), md=3),
                dbc.Col(criar_card_kpi("Comissão Total", formatar_moeda(kpis["comissao_total"]), "💸", COLORS["warning"]), md=3),
                dbc.Col(criar_card_kpi("Qtd Itens Vendidos", f"{kpis['qtd_itens']:,.0f}".replace(",", "."), "📦", COLORS["secondary"]), md=3),
            ], className="g-3 mb-4")

            fig_grupo = grafico_faturamento_por_grupo(df)
            fig_vendedor = grafico_vendedor_comissao(df)
            fig_temporal = grafico_faturamento_temporal(df)
            fig_doc = grafico_por_tipo_documento(df)

            tabela = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns if c not in ["HORAS"]],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "backgroundColor": COLORS["surface"], "color": COLORS["text"]},
                style_header={"backgroundColor": COLORS["surface2"], "fontWeight": "bold", "color": COLORS["text"]},
            )

            # Para formatação de exibição das datas na tabela
            df_tabela = df.copy()
            if "DAT_CHE" in df_tabela.columns:
                df_tabela["DAT_CHE"] = df_tabela["DAT_CHE"].dt.strftime("%d/%m/%Y")

            # Formata colunas de valor na tabela
            cols_formatar = ["PRECO", "TOTALPRODUTO", "ACRESCIMO", "VALCOMISSAO", "CUSTO", "TOTALACRESCIMO"]
            for col in cols_formatar:
                if col in df_tabela.columns:
                    df_tabela[col] = df_tabela[col].apply(formatar_moeda)

            tabela.data = df_tabela.to_dict("records")

            conteudo = [
                dbc.Row([
                    dbc.Col([html.H5("Evolução Temporal do Faturamento"), dcc.Graph(figure=fig_temporal)], md=8),
                    dbc.Col([html.H5("Faturamento por Tipo de Documento"), dcc.Graph(figure=fig_doc)], md=4),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([html.H5("Faturamento e Comissão por Vendedor"), dcc.Graph(figure=fig_vendedor)], md=6),
                    dbc.Col([html.H5("Top 15 Grupos de Produtos"), dcc.Graph(figure=fig_grupo)], md=6),
                ], className="mb-4"),
                html.Hr(),
                html.H5("Detalhamento do Faturamento por Estoque"),
                tabela
            ]

            return kpi_row, conteudo

        return dash.no_update, html.P("Relatório em desenvolvimento...")

    except Exception as e:
        print(f"❌ ERRO NO CALLBACK RELATORIOS: {str(e)}")
        traceback.print_exc()
        return dash.no_update, [html.Div(f"Erro ao processar relatório: {str(e)}", className="text-danger")]


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
        showarrow=False, font=dict(size=14, color=COLORS["neutral"]),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, showgrid=False, zeroline=False), 
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(color=COLORS["text"])
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
    print(f"  [START] {APP_CONFIG['title']}")
    print("="*60)
    print(f"  Acesse: http://localhost:{APP_CONFIG['port']}")
    print(f"  Na rede: http://SEU_IP:{APP_CONFIG['port']}")
    print("="*60 + "\n")

    app.run(
        debug=APP_CONFIG["debug"],
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"],
    )
