"""Download das séries (Banco Central/SGS, IBGE/SIDRA, Yahoo) com cache e tratamento de erros."""
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st

import macro_core as core
from catalogo import CATALOGO

HEADERS = {"User-Agent": "painel-b3/2.0 (uso educacional)"}
ANOS_HISTORICO = 15
SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados"
SIDRA_URL = "https://apisidra.ibge.gov.br/values/{path}"


def _get_json(url, params=None, tentativas=2):
    ultimo = None
    for _ in range(tentativas):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:120]}")
            return r.json()
        except Exception as e:  # rede, JSON inválido, HTTP != 200
            ultimo = e
    raise RuntimeError(str(ultimo))


def _baixar_sgs(codigo: str) -> pd.DataFrame:
    fim = date.today()
    ini = date(fim.year - ANOS_HISTORICO, 1, 1)
    partes = []
    for a, b in core.janelas(ini, fim):
        linhas = _get_json(SGS_URL.format(cod=codigo), {
            "formato": "json", "dataInicial": a.strftime("%d/%m/%Y"), "dataFinal": b.strftime("%d/%m/%Y")})
        if isinstance(linhas, list):
            partes.append(core.parse_sgs(linhas))
    partes = [p for p in partes if not p.empty]
    if not partes:
        return core.vazio()
    return pd.concat(partes).drop_duplicates("data").sort_values("data").reset_index(drop=True)


def _baixar_sidra(path: str, palavras: tuple) -> pd.DataFrame:
    return core.parse_sidra(_get_json(SIDRA_URL.format(path=path)), palavras)


def _baixar_yf(simbolo: str) -> pd.DataFrame:
    import yfinance as yf
    h = yf.Ticker(simbolo).history(period=f"{ANOS_HISTORICO}y", interval="1d")
    if h is None or h.empty:
        return core.vazio()
    idx = h.index.tz_localize(None) if h.index.tz is not None else h.index
    return pd.DataFrame({"data": pd.to_datetime(idx).normalize(), "valor": h["Close"].values}).dropna()


@st.cache_data(ttl=3600, show_spinner=False)
def _serie_cache(sid: str) -> pd.DataFrame:
    """Levanta exceção em caso de erro, para que erros NÃO fiquem em cache."""
    s = CATALOGO[sid]
    if s.tipo == "sgs":
        df = _baixar_sgs(s.ref)
    elif s.tipo == "sidra":
        df = _baixar_sidra(s.ref, s.palavras)
    else:
        df = _baixar_yf(s.ref)
    if df.empty:
        raise RuntimeError("A fonte não retornou dados para esta série.")
    return df


def carregar_serie(sid: str) -> dict:
    """{'df': DataFrame, 'erro': str|None, 'baixado_em': datetime}. Nunca substitui dado ausente por zero."""
    try:
        return {"df": _serie_cache(sid), "erro": None, "baixado_em": datetime.now()}
    except Exception as e:
        return {"df": core.vazio(), "erro": str(e)[:300], "baixado_em": datetime.now()}


def diagnosticar(ids=None, progresso=None) -> pd.DataFrame:
    ids = list(ids or CATALOGO)
    linhas = []
    for i, sid in enumerate(ids):
        s = CATALOGO[sid]
        r = carregar_serie(sid)
        df = r["df"]
        linhas.append({
            "Série": s.nome, "Fonte": s.fonte, "Código": s.ref if s.tipo != "sidra" else s.ref.split("/")[1],
            "Confiança no código": s.confianca,
            "Status": "OK" if r["erro"] is None else "Falhou",
            "Última data": df["data"].iloc[-1].strftime("%d/%m/%Y") if not df.empty else "—",
            "Observações": len(df), "Detalhe": r["erro"] or "",
        })
        if progresso:
            progresso((i + 1) / len(ids))
    return pd.DataFrame(linhas)
