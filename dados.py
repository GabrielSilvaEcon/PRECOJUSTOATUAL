"""Dados de empresas (Yahoo Finance). Funções originais preservadas; novas: dividendos por ano,
demonstrativos anuais/trimestrais, validação e pesquisa de tickers."""
import re
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

PADRAO_TICKER = re.compile(r"^[A-Z]{4}\d{1,2}$")


def normaliza(t: str) -> str:
    return t.upper().strip().replace(".SA", "")


# ---------------------------------------------------------------- cadastro
@st.cache_data(ttl=3600, show_spinner=False)
def validar_ticker(ticker: str):
    """True = encontrou cotação; False = não encontrou (ticker inexistente OU sem conexão)."""
    try:
        h = yf.Ticker(f"{ticker}.SA").history(period="5d")
    except Exception:
        return False
    return h is not None and not h.empty


def pesquisar_nome(consulta: str) -> list:
    """Busca por nome no Yahoo e devolve só papéis da B3 (.SA). Lista vazia se indisponível."""
    try:
        quotes = yf.Search(consulta, max_results=15).quotes
    except Exception:
        return []
    out = []
    for q in quotes or []:
        sym = str(q.get("symbol", ""))
        if sym.endswith(".SA"):
            out.append({"ticker": sym[:-3], "nome": q.get("shortname") or q.get("longname") or sym})
    return out


# ---------------------------------------------------------------- empresa
@st.cache_data(ttl=900, show_spinner=False)
def buscar(ticker: str) -> dict:
    """Cotação, LPA, VPA, dividendos e indicadores (Yahoo Finance, tickers .SA)."""
    t = yf.Ticker(f"{ticker}.SA")
    try:
        info = t.info or {}
    except Exception:
        info = {}

    preco = info.get("currentPrice") or info.get("regularMarketPrice")
    if not preco:
        h = t.history(period="5d")
        preco = float(h["Close"].iloc[-1]) if not h.empty else None

    por_ano = pd.Series(dtype=float)
    div_12m = None
    divs = t.dividends
    if divs is not None and not divs.empty:
        idx = divs.index.tz_localize(None) if divs.index.tz is not None else divs.index
        serie = pd.Series(divs.values, index=idx)
        por_ano = serie.groupby(serie.index.year).sum()
        por_ano = por_ano[por_ano.index < datetime.now().year].tail(5)
        div_12m = float(serie[serie.index >= datetime.now() - timedelta(days=365)].sum())

    return {
        "ticker": ticker,
        "nome": info.get("shortName") or info.get("longName") or ticker,
        "preco": preco,
        "lpa": info.get("trailingEps"),
        "vpa": info.get("bookValue"),
        "div_ano": por_ano,
        "div_medio": float(por_ano.mean()) if len(por_ano) else None,
        "div_12m": div_12m,
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "roe": info.get("returnOnEquity"),
        "margem_liq": info.get("profitMargins"),
        "div_pl": info.get("debtToEquity"),
        "acoes": info.get("sharesOutstanding"),
        "moeda": info.get("financialCurrency") or "BRL",
        "setor_yahoo": info.get("sector"),
        "industria_yahoo": info.get("industry"),
    }


@st.cache_data(ttl=900, show_spinner=False)
def buscar_caixa(ticker: str) -> pd.DataFrame:
    """Fluxo de caixa anual (operacional, capex, livre) por ano."""
    try:
        cf = yf.Ticker(f"{ticker}.SA").cashflow
    except Exception:
        return pd.DataFrame()
    if cf is None or cf.empty:
        return pd.DataFrame()
    nomes = {
        "Operating Cash Flow": "Caixa operacional",
        "Capital Expenditure": "Capex",
        "Free Cash Flow": "Fluxo de caixa livre",
    }
    out = pd.DataFrame({pt: cf.loc[k] for k, pt in nomes.items() if k in cf.index})
    if out.empty:
        return out
    if "Fluxo de caixa livre" not in out and {"Caixa operacional", "Capex"} <= set(out.columns):
        out["Fluxo de caixa livre"] = out["Caixa operacional"] + out["Capex"]
    out.index = pd.to_datetime(out.index).year
    return out.sort_index()


@st.cache_data(ttl=900, show_spinner=False)
def buscar_dividendos(ticker: str) -> pd.Series:
    """Dividendos por ação somados por ano, TODO o histórico (inclui o ano corrente, que é parcial)."""
    try:
        divs = yf.Ticker(f"{ticker}.SA").dividends
    except Exception:
        return pd.Series(dtype=float)
    if divs is None or divs.empty:
        return pd.Series(dtype=float)
    idx = divs.index.tz_localize(None) if divs.index.tz is not None else divs.index
    return pd.Series(divs.values, index=idx).groupby(idx.year).sum()


_LINHAS = {
    "Receita": ["Total Revenue", "Operating Revenue"],
    "Lucro operacional": ["Operating Income"],
    "EBITDA": ["EBITDA", "Normalized EBITDA"],
    "Lucro líquido": ["Net Income", "Net Income Common Stockholders"],
    "Caixa operacional": ["Operating Cash Flow"],
    "Capex": ["Capital Expenditure"],
    "Fluxo de caixa livre": ["Free Cash Flow"],
}


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_demonstrativos(ticker: str, freq: str) -> pd.DataFrame:
    """Demonstrativos por período. `freq`: 'anual' ou 'trimestral'. Índice = data de fechamento do período.
    Linhas que o Yahoo não informa ficam ausentes (NaN) — nunca zero."""
    t = yf.Ticker(f"{ticker}.SA")
    try:
        if freq == "anual":
            dre, cx = t.income_stmt, t.cashflow
        else:
            dre, cx = t.quarterly_income_stmt, t.quarterly_cashflow
    except Exception:
        return pd.DataFrame()
    fontes = [x for x in (dre, cx) if x is not None and not x.empty]
    if not fontes:
        return pd.DataFrame()
    cols = {}
    for nome, candidatos in _LINHAS.items():
        for fonte in fontes:
            achou = next((c for c in candidatos if c in fonte.index), None)
            if achou:
                cols[nome] = fonte.loc[achou]
                break
    if not cols:
        return pd.DataFrame()
    df = pd.DataFrame(cols)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    if "Fluxo de caixa livre" not in df and {"Caixa operacional", "Capex"} <= set(df.columns):
        df["Fluxo de caixa livre"] = df["Caixa operacional"] + df["Capex"]
    df["Ano"] = df.index.year
    return df


@st.cache_data(ttl=900, show_spinner=False)
def historico(ticker: str, periodo: str, intervalo: str) -> pd.DataFrame:
    try:
        h = yf.Ticker(f"{ticker}.SA").history(period=periodo, interval=intervalo, auto_adjust=False)
    except Exception:
        return pd.DataFrame()
    return _limpa(h)


@st.cache_data(ttl=900, show_spinner=False)
def historico_intervalo(ticker: str, ini: str, fim: str, intervalo: str) -> pd.DataFrame:
    """Histórico entre duas datas ISO (usado quando a análise técnica segue o filtro de anos)."""
    try:
        h = yf.Ticker(f"{ticker}.SA").history(start=ini, end=fim, interval=intervalo, auto_adjust=False)
    except Exception:
        return pd.DataFrame()
    return _limpa(h)


def _limpa(h):
    if h is None or h.empty:
        return pd.DataFrame()
    h = h[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open", "High", "Low", "Close"])
    h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
    return h


def carregar(ativos):
    out = {}
    with st.spinner("Buscando dados..."):
        for tk in ativos:
            try:
                out[tk] = buscar(tk)
            except Exception as e:
                st.warning(f"Não consegui carregar {tk}: {e}")
    return out
