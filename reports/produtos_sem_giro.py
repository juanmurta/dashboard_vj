# =============================================================================
# reports/produtos_sem_giro.py — Processamento do relatório de Produtos sem Giro
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import executar_query_por_coligadas
from database.queries import SQL_PRODUTOS_SEM_GIRO
from config import COLORS, COLOR_SEQUENCE


def buscar_produtos_sem_giro(coligada: str, dias: int) -> pd.DataFrame:
    """
    Busca os produtos sem giro no banco de dados.
    """
    # Garante que DIAS seja negativo (se o usuário digitar positivo, invertemos)
    if dias > 0:
        dias = -dias
    elif dias == 0:
        dias = -90  # Default

    parametros = {
        "DIAS": dias
    }

    df = executar_query_por_coligadas(SQL_PRODUTOS_SEM_GIRO, parametros, "codemp", coligada)

    if df.empty:
        return df

    # Tratamento de tipos numéricos
    for col in ["ESTOQUE", "PRECO_VENDA", "PRECO_CUSTO"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Cálculo de valor total em estoque (a preço de custo)
    df["VALOR_ESTOQUE"] = df["ESTOQUE"] * df["PRECO_CUSTO"]

    return df


def calcular_kpis_sem_giro(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores para o relatório de produtos sem giro.
    """
    if df.empty:
        return {
            "total_itens": 0,
            "valor_parado": 0.0,
            "estoque_total": 0,
            "grupos_afetados": 0
        }

    return {
        "total_itens": len(df),
        "valor_parado": df["VALOR_ESTOQUE"].sum(),
        "estoque_total": df["ESTOQUE"].sum(),
        "grupos_afetados": df["GRUPO"].nunique()
    }


def grafico_por_grupo(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: valor parado por grupo.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_grupo = df.groupby("GRUPO")["VALOR_ESTOQUE"].sum().reset_index()
    df_grupo = df_grupo.sort_values("VALOR_ESTOQUE", ascending=False).head(15)

    fig = px.bar(
        df_grupo,
        x="VALOR_ESTOQUE",
        y="GRUPO",
        orientation="h",
        color_discrete_sequence=[COLORS["primary"]],
        labels={"VALOR_ESTOQUE": "Valor Parado (R$)", "GRUPO": "Grupo"},
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
