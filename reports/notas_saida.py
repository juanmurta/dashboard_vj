# =============================================================================
# reports/notas_saida.py — Relatório de Notas de Saída
# =============================================================================
# Este módulo tem duas responsabilidades:
#   1. Buscar e tratar os dados do banco (via database/)
#   2. Gerar os gráficos Plotly prontos para o Dash exibir
#
# Cada relatório tem seu próprio arquivo nesta pasta.
# O app.py apenas chama as funções daqui — não conhece SQL nem Plotly.
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from database.connection import executar_query_por_coligadas
from database.queries import SQL_NOTAS_SAIDA
from config import COLORS, COLOR_SEQUENCE


# =============================================================================
# CAMADA DE DADOS — Busca e prepara o DataFrame
# =============================================================================

def buscar_notas(coligada: str, data_ini: str, data_fim: str) -> pd.DataFrame:
    """
    Busca as notas de saída no banco e retorna um DataFrame tratado.

    Args:
        coligada  (int): Código da empresa/coligada
        data_ini  (str): Data inicial no formato 'YYYY-MM-DD'
        data_fim  (str): Data final no formato 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: Dados prontos para análise e geração de gráficos.
                      Retorna DataFrame vazio se não encontrar dados.
    """
    parametros = {
        "pdatai": data_ini,
        "pdataf": data_fim,
    }

    df = executar_query_por_coligadas(SQL_NOTAS_SAIDA, parametros, "pcodemp", coligada)

    if df.empty:
        return df

    # -------------------------------------------------------------------------
    # TRATAMENTO DOS DADOS
    # Faça aqui todas as transformações necessárias antes de plotar.
    # -------------------------------------------------------------------------

    # Garante que datas sejam do tipo datetime (para agrupamentos e filtros)
    df["DAT_EMI"] = pd.to_datetime(df["DAT_EMI"], errors="coerce")
    df["DAT_CHE"] = pd.to_datetime(df["DAT_CHE"], errors="coerce")

    # Remove linhas onde DAT_EMI é NaT para evitar erros de agrupamento temporal
    df = df.dropna(subset=["DAT_EMI"])

    # Garante que VALOR seja numérico (Firebird às vezes retorna Decimal)
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)

    # Cria coluna de mês/ano para agrupamentos temporais
    df["MES_ANO"] = df["DAT_EMI"].dt.to_period("M").astype(str)

    # Normaliza o status de cancelamento
    # (Firebird pode retornar 'S', 'N', None — padronizamos para Sim/Não)
    df["STATUS_CANCEL"] = df["CANCELADO"].apply(
        lambda x: "Cancelada" if str(x).strip().upper() == "S" else "Ativa"
    )

    # Normaliza o status de fechamento
    df["STATUS_FECHADO"] = df["FECHADO"].apply(
        lambda x: "Fechada" if str(x).strip().upper() == "S" else "Aberta"
    )

    return df


def calcular_kpis(df: pd.DataFrame) -> dict:
    """
    Calcula os indicadores-chave (KPIs) exibidos nos cards do topo.

    Args:
        df (pd.DataFrame): DataFrame retornado por buscar_notas()

    Returns:
        dict: Dicionário com os KPIs calculados.
    """
    if df.empty:
        return {
            "total_notas": 0,
            "valor_total": 0.0,
            "ticket_medio": 0.0,
            "notas_ativas": 0,
            "notas_canceladas": 0,
            "clientes_unicos": 0,
        }

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"]

    return {
        "total_notas": len(df),
        "valor_total": df_ativas["VALOR"].sum(),
        "ticket_medio": df_ativas["VALOR"].mean() if len(df_ativas) > 0 else 0,
        "notas_ativas": len(df_ativas),
        "notas_canceladas": len(df[df["STATUS_CANCEL"] == "Cancelada"]),
        "clientes_unicos": df_ativas["CODCLI"].nunique(),
    }


# =============================================================================
# CAMADA DE VISUALIZAÇÃO — Gera os gráficos Plotly
# =============================================================================

# Configuração visual padrão aplicada a todos os gráficos
_LAYOUT_PADRAO = dict(
    paper_bgcolor="rgba(0,0,0,0)",  # Fundo transparente (herda do CSS)
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
    ),
)


def grafico_faturamento_diario(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de linha: evolução do faturamento dia a dia.
    Mostra apenas notas ativas.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"].copy()

    # Agrupa por data e soma o valor
    por_dia = (
        df_ativas.groupby("DAT_EMI")["VALOR"]
        .sum()
        .reset_index()
        .sort_values("DAT_EMI")
    )

    fig = px.line(
        por_dia,
        x="DAT_EMI",
        y="VALOR",
        title="Faturamento Diário",
        labels={"DAT_EMI": "Data", "VALOR": "Valor (R$)"},
        color_discrete_sequence=[COLORS["primary"]],
        markers=True,  # Pontos nos vértices da linha
    )

    # Área preenchida sob a linha
    fig.update_traces(fill="tozeroy", fillcolor=f"rgba(37,99,235,0.15)")

    # Formata o eixo Y como moeda
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", gridcolor="rgba(255,255,255,0.07)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)")
    fig.update_layout(**_LAYOUT_PADRAO)

    return fig


def grafico_por_vendedor(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras horizontais: ranking de faturamento por vendedor.
    Top 10 vendedores do período.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"].copy()

    por_vendedor = (
        df_ativas.groupby("NOMFUN")["VALOR"]
        .sum()
        .reset_index()
        .sort_values("VALOR", ascending=True)  # ascending=True → maior fica no topo
        .tail(10)  # Top 10
    )

    fig = px.bar(
        por_vendedor,
        x="VALOR",
        y="NOMFUN",
        orientation="h",  # Horizontal
        title="Top 10 Vendedores por Faturamento",
        labels={"NOMFUN": "Vendedor", "VALOR": "Valor (R$)"},
        color="VALOR",
        color_continuous_scale=["#1E3A5F", COLORS["primary"]],
        text_auto=".2s",  # Mostra o valor dentro da barra
    )

    fig.update_xaxes(tickprefix="R$ ", tickformat=",.2f", gridcolor="rgba(255,255,255,0.07)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)")
    fig.update_traces(textfont_color=COLORS["text"])
    fig.update_layout(**_LAYOUT_PADRAO, coloraxis_showscale=False)

    return fig


def grafico_por_classificacao(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pizza/donut: distribuição do faturamento por tipo de venda.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"].copy()

    por_tipo = (
        df_ativas.groupby("CLASSIFICACAO")["VALOR"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        por_tipo,
        names="CLASSIFICACAO",
        values="VALOR",
        title="Faturamento por Classificação de Venda",
        hole=0.45,  # hole > 0 = donut chart
        color_discrete_sequence=COLOR_SEQUENCE,
    )

    fig.update_traces(
        textinfo="label+percent",
        textfont_size=12,
        marker=dict(line=dict(color=COLORS["background"], width=2)),
    )
    fig.update_layout(**_LAYOUT_PADRAO)

    return fig


def grafico_por_forma_pagamento(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: faturamento agrupado por forma de pagamento.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"].copy()

    por_pag = (
        df_ativas.groupby("FORMAPAG")["VALOR"]
        .sum()
        .reset_index()
        .sort_values("VALOR", ascending=False)
    )

    fig = px.bar(
        por_pag,
        x="FORMAPAG",
        y="VALOR",
        title="Faturamento por Forma de Pagamento",
        labels={"FORMAPAG": "Forma de Pagamento", "VALOR": "Valor (R$)"},
        color="FORMAPAG",
        color_discrete_sequence=COLOR_SEQUENCE,
        text_auto=".2s",
    )

    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", gridcolor="rgba(255,255,255,0.07)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)")
    fig.update_layout(**_LAYOUT_PADRAO, showlegend=False)

    return fig


def grafico_por_cidade(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Gráfico de barras: top cidades por faturamento.

    Args:
        df    (pd.DataFrame): Dados do relatório
        top_n (int): Quantidade de cidades a exibir (padrão: 15)
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    df_ativas = df[df["STATUS_CANCEL"] == "Ativa"].copy()

    por_cidade = (
        df_ativas.groupby("CIDADE")["VALOR"]
        .sum()
        .reset_index()
        .sort_values("VALOR", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        por_cidade,
        x="CIDADE",
        y="VALOR",
        title=f"Top {top_n} Cidades por Faturamento",
        labels={"CIDADE": "Cidade", "VALOR": "Valor (R$)"},
        color="VALOR",
        color_continuous_scale=["#1A3A2A", COLORS["success"]],
        text_auto=".2s",
    )

    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", gridcolor="rgba(255,255,255,0.07)")
    fig.update_xaxes(tickangle=-35, gridcolor="rgba(255,255,255,0.07)")
    fig.update_layout(**_LAYOUT_PADRAO, coloraxis_showscale=False)

    return fig


def grafico_canceladas_vs_ativas(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras empilhadas por mês: notas ativas vs canceladas.
    Mostra o impacto das cancelamentos no período.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para o período selecionado")

    por_mes_status = (
        df.groupby(["MES_ANO", "STATUS_CANCEL"])
        .agg(QUANTIDADE=("NOTA", "count"), VALOR=("VALOR", "sum"))
        .reset_index()
    )

    fig = px.bar(
        por_mes_status,
        x="MES_ANO",
        y="VALOR",
        color="STATUS_CANCEL",
        title="Ativas vs Canceladas por Mês (R$)",
        labels={"MES_ANO": "Mês", "VALOR": "Valor (R$)", "STATUS_CANCEL": "Status"},
        barmode="stack",
        color_discrete_map={
            "Ativa": COLORS["primary"],
            "Cancelada": COLORS["danger"],
        },
        text_auto=".2s",
    )

    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", gridcolor="rgba(255,255,255,0.07)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)")
    fig.update_layout(**_LAYOUT_PADRAO)

    return fig


# =============================================================================
# UTILITÁRIOS INTERNOS
# =============================================================================

def _grafico_vazio(mensagem: str) -> go.Figure:
    """
    Retorna um gráfico vazio com uma mensagem amigável.
    Usado quando o banco não retorna dados para o período selecionado.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=mensagem,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS["neutral"]),
    )
    fig.update_layout(
        **_LAYOUT_PADRAO,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
    )
    return fig
