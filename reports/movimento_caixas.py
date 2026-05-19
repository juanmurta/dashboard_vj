# =============================================================================
# reports/movimento_caixas.py — Processamento do relatório de Movimento de Caixas
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import executar_query
from database.queries import SQL_MOVIMENTO_CAIXAS
from config import COLORS, COLOR_SEQUENCE

def buscar_movimento_caixas(data_ini: str, data_fim: str) -> pd.DataFrame:
    """
    Busca o movimento de caixas e bancos no banco de dados.
    """
    parametros = {
        "pdatai": data_ini,
        "pdataf": data_fim
    }

    df = executar_query(SQL_MOVIMENTO_CAIXAS, parametros)

    if df.empty:
        return df

    # Garante colunas em maiúsculas
    df.columns = [c.upper() for c in df.columns]

    # Tratamento de tipos
    if "VALOR" in df.columns:
        df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)
    
    if "DATAMOV" in df.columns:
        df["DATAMOV"] = pd.to_datetime(df["DATAMOV"])

    # Ajuste de valores: Tipos de lançamento (Entrada/Saída)
    # No banco, parece que 'C' (Crédito) é Entrada e 'D' (Débito) é Saída.
    if "VALOR" in df.columns and "DC" in df.columns:
        df["VALOR_SINAL"] = df.apply(
            lambda x: abs(x["VALOR"]) if str(x["DC"]).strip().upper() == "C" else -abs(x["VALOR"]), axis=1
        )
    else:
        df["VALOR_SINAL"] = 0.0

    return df

def calcular_kpis_movimento(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores para o relatório de movimento de caixas.
    """
    if df.empty:
        return {
            "total_entradas": 0.0,
            "total_saidas": 0.0,
            "saldo_periodo": 0.0,
            "n_lancamentos": 0
        }

    # 'C' = Crédito (Entrada), 'D' = Débito (Saída)
    entradas = df[df["DC"].str.strip().str.upper() == "C"]["VALOR"].abs().sum()
    saidas = df[df["DC"].str.strip().str.upper() == "D"]["VALOR"].abs().sum()
    saldo = entradas - saidas

    return {
        "total_entradas": entradas,
        "total_saidas": saidas,
        "saldo_periodo": saldo,
        "n_lancamentos": len(df)
    }

def grafico_entradas_saidas_pizza(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pizza comparando total de entradas e saídas.
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    resumo = df.groupby("DC")["VALOR"].sum().abs().reset_index()
    resumo["DC"] = resumo["DC"].str.strip().str.upper().map({"C": "Entradas", "D": "Saídas"})
    resumo = resumo.dropna(subset=["DC"])

    fig = px.pie(
        resumo,
        values="VALOR",
        names="DC",
        color="DC",
        color_discrete_map={"Entradas": COLORS["success"], "Saídas": COLORS["danger"]},
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

def grafico_movimentacao_diaria(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras empilhadas por dia (Entradas e Saídas).
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    df_diario = df.groupby([df["DATAMOV"].dt.date, "DC"])["VALOR"].sum().abs().reset_index()
    df_diario["DC"] = df_diario["DC"].str.strip().str.upper().map({"C": "Entradas", "D": "Saídas"})
    df_diario = df_diario.dropna(subset=["DC"])

    fig = px.bar(
        df_diario,
        x="DATAMOV",
        y="VALOR",
        color="DC",
        barmode="group",
        color_discrete_map={"Entradas": COLORS["success"], "Saídas": COLORS["danger"]},
        labels={"VALOR": "Valor (R$)", "DATAMOV": "Data", "DC": "Tipo"}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def grafico_por_caixa_banco(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: movimentação por Caixa/Banco.
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    # Usa NOME_ORIGEM que veio da query (CADBANCO.banco)
    if "NOME_ORIGEM" not in df.columns:
        df["NOME_ORIGEM"] = "NÃO IDENTIFICADO"
    else:
        df["NOME_ORIGEM"] = df["NOME_ORIGEM"].fillna("NÃO IDENTIFICADO")
    
    df_origem = df.groupby("NOME_ORIGEM")["VALOR"].sum().abs().reset_index()
    df_origem = df_origem.sort_values("VALOR", ascending=False).head(10)

    fig = px.bar(
        df_origem,
        x="VALOR",
        y="NOME_ORIGEM",
        orientation="h",
        color_discrete_sequence=[COLORS["primary"]],
        labels={"VALOR": "Volume Total (R$)", "NOME_ORIGEM": "Caixa / Banco"}
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

def grafico_saldo_acumulado(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de linha: evolução do saldo no período.
    """
    if df.empty:
        return _grafico_vazio("Sem dados")

    df_saldo = df.groupby(df["DATAMOV"].dt.date)["VALOR_SINAL"].sum().reset_index()
    df_saldo = df_saldo.sort_values("DATAMOV")
    df_saldo["SALDO_ACUMULADO"] = df_saldo["VALOR_SINAL"].cumsum()

    fig = px.line(
        df_saldo,
        x="DATAMOV",
        y="SALDO_ACUMULADO",
        color_discrete_sequence=[COLORS["secondary"]],
        labels={"SALDO_ACUMULADO": "Saldo Acumulado (R$)", "DATAMOV": "Data"}
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
