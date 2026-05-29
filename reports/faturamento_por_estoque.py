# =============================================================================
# reports/faturamento_por_estoque.py — Processamento de Faturamento por Estoque
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import executar_query_por_coligadas
from database.queries import SQL_FATURAMENTO_POR_ESTOQUE
from config import COLORS, COLOR_SEQUENCE


def buscar_faturamento_por_estoque(coligada: str, data_ini: str, data_fim: str) -> pd.DataFrame:
    """
    Busca os dados de faturamento por estoque no banco de dados.
    """
    parametros = {
        "DATAI": data_ini,
        "DATAF": data_fim,
    }

    df = executar_query_por_coligadas(SQL_FATURAMENTO_POR_ESTOQUE, parametros, "COLIGADA", coligada)

    if df.empty:
        return df

    # Garantir nomes de colunas em maiúsculo para consistência
    df.columns = [c.upper() for c in df.columns]

    # Tratamento de tipos numéricos
    cols_numericas = [
        "QUANT", "PRECO", "TOTALPRODUTO", "DESCONTO",
        "PERCOMISSAO", "VALCOMISSAO", "CUSTO", "ACRESCIMO", "TOTALACRESCIMO"
    ]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Tratamento de tipos de data
    if "DAT_CHE" in df.columns:
        df["DAT_CHE"] = pd.to_datetime(df["DAT_CHE"], errors="coerce")

    return df


def calcular_kpis_faturamento(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores para o relatório de faturamento por estoque.
    """
    if df.empty:
        return {
            "faturamento_total": 0.0,
            "margem_bruta": 0.0,
            "comissao_total": 0.0,
            "qtd_itens": 0.0
        }

    faturamento_total = df["TOTALACRESCIMO"].sum()
    custo_total = (df["CUSTO"] * df["QUANT"]).sum()
    margem_bruta = faturamento_total - custo_total
    comissao_total = df["VALCOMISSAO"].sum()
    qtd_itens = df["QUANT"].sum()

    return {
        "faturamento_total": faturamento_total,
        "margem_bruta": margem_bruta,
        "comissao_total": comissao_total,
        "qtd_itens": qtd_itens
    }


def grafico_faturamento_por_grupo(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: Faturamento por Grupo de Produtos (Top 15).
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_grupo = df.groupby("GRUPO")["TOTALACRESCIMO"].sum().reset_index()
    df_grupo = df_grupo.sort_values("TOTALACRESCIMO", ascending=True).tail(15)

    fig = px.bar(
        df_grupo,
        x="TOTALACRESCIMO",
        y="GRUPO",
        orientation="h",
        color_discrete_sequence=[COLORS["primary"]],
        labels={"TOTALACRESCIMO": "Faturamento (R$)", "GRUPO": "Grupo de Produtos"},
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


def grafico_vendedor_comissao(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras e linhas: Faturamento (Eixo Y1) vs Comissão (Eixo Y2) por Vendedor.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_vendedor = df.groupby("NOMFUN").agg({
        "TOTALACRESCIMO": "sum",
        "VALCOMISSAO": "sum"
    }).reset_index()

    df_vendedor = df_vendedor.sort_values("TOTALACRESCIMO", ascending=False).head(10)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_vendedor["NOMFUN"],
        y=df_vendedor["TOTALACRESCIMO"],
        name="Faturamento (R$)",
        marker_color=COLORS["success"],
        yaxis="y1"
    ))

    fig.add_trace(go.Scatter(
        x=df_vendedor["NOMFUN"],
        y=df_vendedor["VALCOMISSAO"],
        name="Comissão (R$)",
        mode="lines+markers",
        line=dict(color=COLORS["warning"], width=3),
        marker=dict(size=8),
        yaxis="y2"
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        yaxis=dict(
            title=dict(
                text="Faturamento (R$)",
                font=dict(color=COLORS["success"])
            ),
            tickfont=dict(color=COLORS["success"]),
            gridcolor="rgba(255,255,255,0.07)"
        ),
        yaxis2=dict(
            title=dict(
                text="Comissão (R$)",
                font=dict(color=COLORS["warning"])
            ),
            tickfont=dict(color=COLORS["warning"]),
            overlaying="y",
            side="right"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def grafico_faturamento_temporal(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de linha: Evolução Temporal do Faturamento por data de entrega/chegada.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_temporal = df.groupby(df["DAT_CHE"].dt.date)["TOTALACRESCIMO"].sum().reset_index()
    df_temporal = df_temporal.sort_values("DAT_CHE")

    fig = px.line(
        df_temporal,
        x="DAT_CHE",
        y="TOTALACRESCIMO",
        color_discrete_sequence=[COLORS["secondary"]],
        labels={"TOTALACRESCIMO": "Faturamento (R$)", "DAT_CHE": "Data de Chegada"}
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


def grafico_por_tipo_documento(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de rosca: Faturamento por Tipo de Documento/Conta.
    """
    if df.empty:
        return _grafico_vazio("Sem dados para exibir")

    df_doc = df.groupby("DESTIP")["TOTALACRESCIMO"].sum().reset_index()
    df_doc = df_doc.sort_values("TOTALACRESCIMO", ascending=False)

    fig = px.pie(
        df_doc,
        values="TOTALACRESCIMO",
        names="DESTIP",
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
