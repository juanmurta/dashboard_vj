# =============================================================================
# reports/posicao_estoque_vendas.py — Processamento do relatório de Posição de Estoque vs. Vendas
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import executar_query_por_coligadas
from database.queries import SQL_POSICAO_ESTOQUE_VENDAS
from config import COLORS, COLOR_SEQUENCE


def buscar_posicao_estoque_vendas(coligada: str) -> pd.DataFrame:
    """
    Busca a posição de estoque vs vendas no banco de dados.
    """
    parametros = {
    }

    df = executar_query_por_coligadas(SQL_POSICAO_ESTOQUE_VENDAS, parametros, "COLIGADA", coligada)

    if df.empty:
        return df

    # Garantir nomes de colunas em maiúsculo para consistência
    df.columns = [c.upper() for c in df.columns]

    # Tratamento de tipos numéricos
    cols_numericas = ["ESTOQUE", "ESTMIN", "MEDIO", "CUSTOTOTAL", "TOTALVENDA", "MEDIAESTOQUE"]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def calcular_kpis_posicao(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores para o relatório.
    """
    if df.empty:
        return {
            "total_produtos": 0,
            "custo_total_estoque": 0.0,
            "total_vendas_periodo": 0.0,
            "itens_abaixo_minimo": 0
        }

    return {
        "total_produtos": len(df),
        "custo_total_estoque": df["CUSTOTOTAL"].sum(),
        "total_vendas_periodo": df["TOTALVENDA"].sum(),
        "itens_abaixo_minimo": len(df[df["ESTOQUE"] < df["ESTMIN"]])
    }


def grafico_custo_por_grupo(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pizza: Custo Total por Grupo.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_grupo = df.groupby("GRUPO")["CUSTOTOTAL"].sum().reset_index()
    df_grupo = df_grupo.sort_values("CUSTOTOTAL", ascending=False).head(10)

    fig = px.pie(
        df_grupo,
        values="CUSTOTOTAL",
        names="GRUPO",
        color_discrete_sequence=COLOR_SEQUENCE,
        hole=0.4,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=50, r=50, t=50, b=100),  # Aumentado o espaçamento
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,  # Movida mais para baixo para não sobrepor
            xanchor="center",
            x=0.5
        )
    )
    # Garante que os rótulos de texto fiquem fora das fatias se forem grandes
    fig.update_traces(textposition='outside', textinfo='percent+label')
    return fig


def grafico_vendas_vs_estoque(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: Top 15 produtos por Venda vs Estoque Atual.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_top = df.sort_values("TOTALVENDA", ascending=False).head(15)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_top["DESPRO"],
        y=df_top["TOTALVENDA"],
        name="Total Vendas (180d)",
        marker_color=COLORS["primary"]
    ))

    fig.add_trace(go.Bar(
        x=df_top["DESPRO"],
        y=df_top["ESTOQUE"],
        name="Estoque Atual",
        marker_color=COLORS["success"]
    ))

    fig.update_layout(
        barmode='group',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)", tickangle=45),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig
