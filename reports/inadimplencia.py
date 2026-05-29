# =============================================================================
# reports/inadimplencia.py — Processamento do relatório de Inadimplência
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import executar_query_por_coligadas
from database.queries import SQL_INADIMPLENCIA_PERIODO
from config import COLORS, COLOR_SEQUENCE


def buscar_inadimplencia(coligada: str, data_ini: str, data_fim: str) -> pd.DataFrame:
    """
    Busca os dados de inadimplência no banco de dados.
    """
    parametros = {
        "DATVEN_INI": data_ini,
        "DATVEN_FIN": data_fim
    }

    df = executar_query_por_coligadas(SQL_INADIMPLENCIA_PERIODO, parametros, "COLIGADA", coligada)

    if df.empty:
        return df

    # Garante colunas em maiúsculas
    df.columns = [c.upper() for c in df.columns]

    # Tratamento de tipos
    if "VRLCONT" in df.columns:
        df["VRLCONT"] = pd.to_numeric(df["VRLCONT"], errors="coerce").fillna(0)
    if "VALJUR" in df.columns:
        df["VALJUR"] = pd.to_numeric(df["VALJUR"], errors="coerce").fillna(0)

    # Total a receber (Valor original + Juros se houver)
    df["VALOR_TOTAL"] = df["VRLCONT"] + df["VALJUR"]

    if "DATVEN" in df.columns:
        df["DATVEN"] = pd.to_datetime(df["DATVEN"])

    if "DATEMI" in df.columns:
        df["DATEMI"] = pd.to_datetime(df["DATEMI"])

    return df


def calcular_kpis_inadimplencia(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores para o relatório de inadimplência.
    """
    if df.empty:
        return {
            "valor_total": 0.0,
            "qtd_titulos": 0,
            "media_atraso": 0,
            "maior_atraso": 0
        }

    total = df["VALOR_TOTAL"].sum()
    qtd = len(df)
    media_atraso = df["DIASATRASO"].mean() if "DIASATRASO" in df.columns else 0
    maior_atraso = df["DIASATRASO"].max() if "DIASATRASO" in df.columns else 0

    return {
        "valor_total": total,
        "qtd_titulos": qtd,
        "media_atraso": int(media_atraso),
        "maior_atraso": int(maior_atraso)
    }


def grafico_por_vendedor(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: Inadimplência por Vendedor.
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    df_vendedor = df.groupby("NOMFUN")["VALOR_TOTAL"].sum().reset_index()
    df_vendedor = df_vendedor.sort_values("VALOR_TOTAL", ascending=False).head(10)

    fig = px.bar(
        df_vendedor,
        x="VALOR_TOTAL",
        y="NOMFUN",
        orientation="h",
        color_discrete_sequence=[COLORS["danger"]],
        labels={"VALOR_TOTAL": "Valor Inadimplente (R$)", "NOMFUN": "Vendedor"}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
    )
    return fig


def grafico_por_cidade(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pizza: Inadimplência por Cidade.
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    df_cidade = df.groupby("CIDCLI")["VALOR_TOTAL"].sum().reset_index()
    df_cidade = df_cidade.sort_values("VALOR_TOTAL", ascending=False).head(10)

    fig = px.pie(
        df_cidade,
        values="VALOR_TOTAL",
        names="CIDCLI",
        color_discrete_sequence=COLOR_SEQUENCE,
        hole=0.4
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def grafico_por_cliente(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: Clientes que mais devem (Top 10).
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    df_cliente = df.groupby("NOMCLI")["VALOR_TOTAL"].sum().reset_index()
    df_cliente = df_cliente.sort_values("VALOR_TOTAL", ascending=False).head(10)

    fig = px.bar(
        df_cliente,
        x="VALOR_TOTAL",
        y="NOMCLI",
        orientation="h",
        color_discrete_sequence=[COLORS["warning"]],
        labels={"VALOR_TOTAL": "Valor Inadimplente (R$)", "NOMCLI": "Cliente"}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
    )
    return fig


def grafico_faixas_atraso(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: Inadimplência por faixa de dias de atraso (abrangente).
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    def categorizar_atraso(dias):
        if dias <= 15: return "00-15 dias"
        if dias <= 30: return "16-30 dias"
        if dias <= 60: return "31-60 dias"
        if dias <= 90: return "61-90 dias"
        if dias <= 180: return "91-180 dias"
        if dias <= 360: return "181-360 dias"
        return "Mais de 1 ano"

    df["FAIXA_ATRASO"] = df["DIASATRASO"].apply(categorizar_atraso)

    ordem = ["00-15 dias", "16-30 dias", "31-60 dias", "61-90 dias", "91-180 dias", "181-360 dias", "Mais de 1 ano"]
    df_faixa = df.groupby("FAIXA_ATRASO")["VALOR_TOTAL"].sum().reindex(ordem).fillna(0).reset_index()

    fig = px.bar(
        df_faixa,
        x="FAIXA_ATRASO",
        y="VALOR_TOTAL",
        color="FAIXA_ATRASO",
        color_discrete_sequence=px.colors.sequential.Reds_r,
        labels={"VALOR_TOTAL": "Valor (R$)", "FAIXA_ATRASO": "Faixa de Atraso"}
    )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
    )
    return fig


def _grafico_vazio(mensagem: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=mensagem,
        showarrow=False,
        font=dict(size=14, color=COLORS["neutral"]),
        xref="paper", yref="paper", x=0.5, y=0.5
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig
