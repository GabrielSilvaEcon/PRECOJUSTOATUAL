"""Estado da sessão: carteira de ações e widgets que LEMBRAM a escolha ao trocar de aba.

Como funciona: o Streamlit apaga o valor de um widget quando ele deixa de ser desenhado. Cada widget
daqui guarda o valor em st.session_state["_p_<chave>"] (persistente) e usa "w_<chave>" como chave do widget.
"""
import json
import os

import streamlit as st

ARQUIVO = "carteira.json"
PADRAO = ["PETR4", "ITSA4", "BBAS3", "VALE3"]


# ---------------------------------------------------------------- widgets persistentes
def _lembrar(c, padrao):
    return st.session_state.setdefault("_p_" + c, padrao)


def _salvar(c):
    st.session_state["_p_" + c] = st.session_state.get("w_" + c)


def definir(c, valor):
    """Altera a escolha lembrada (use dentro de callbacks)."""
    st.session_state["_p_" + c] = valor
    st.session_state.pop("w_" + c, None)


def lembrado(c, padrao=None):
    return st.session_state.get("_p_" + c, padrao)


def selectbox(c, label, opcoes, padrao=None, onde=None, **kw):
    opcoes = list(opcoes)
    v = _lembrar(c, padrao if padrao is not None else (opcoes[0] if opcoes else None))
    if st.session_state.get("w_" + c) not in opcoes:
        st.session_state.pop("w_" + c, None)
    idx = opcoes.index(v) if v in opcoes else 0
    return (onde or st).selectbox(label, opcoes, index=idx, key="w_" + c, on_change=_salvar, args=(c,), **kw)


def multiselect(c, label, opcoes, padrao=None, onde=None, **kw):
    opcoes = list(opcoes)
    v = _lembrar(c, list(padrao) if padrao is not None else [])
    atual = st.session_state.get("w_" + c)
    if atual is not None and any(x not in opcoes for x in atual):
        st.session_state["_p_" + c] = [x for x in atual if x in opcoes]
        st.session_state.pop("w_" + c, None)
        v = st.session_state["_p_" + c]
    return (onde or st).multiselect(label, opcoes, default=[x for x in v if x in opcoes], key="w_" + c,
                          on_change=_salvar, args=(c,), **kw)


def checkbox(c, label, padrao=False, onde=None, **kw):
    v = _lembrar(c, padrao)
    return (onde or st).checkbox(label, value=v, key="w_" + c, on_change=_salvar, args=(c,), **kw)


def slider(c, label, minimo, maximo, padrao, passo, onde=None, **kw):
    v = _lembrar(c, padrao)
    return (onde or st).slider(label, minimo, maximo, v, passo, key="w_" + c, on_change=_salvar, args=(c,), **kw)


def segmentado(c, label, opcoes, padrao=None):
    opcoes = list(opcoes)
    padrao = padrao if padrao is not None else opcoes[0]
    v = _lembrar(c, padrao)
    if v not in opcoes:
        v = padrao
    sel = st.segmented_control(label, opcoes, default=v, key="w_" + c, on_change=_salvar, args=(c,),
                               label_visibility="collapsed")
    if sel is None:               # clique que desmarcou: mantém a escolha anterior
        sel = v
        st.session_state["_p_" + c] = v
    return sel


# ---------------------------------------------------------------- carteira
def _ler_arquivo():
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            d = json.load(f)
        cad = [str(t) for t in d.get("cadastro", [])]
        acomp = [t for t in d.get("acompanhando", cad) if t in cad]
        if cad:
            return cad, acomp
    except Exception:
        pass
    return list(PADRAO), list(PADRAO)


def salvar_carteira():
    """Grava a carteira em carteira.json. Pode falhar em hospedagens somente leitura: sem problema."""
    conteudo = {"cadastro": st.session_state.cadastro, "acompanhando": lembrado("acomp", [])}
    if st.session_state.get("_salvo") == conteudo:
        return
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(conteudo, f, ensure_ascii=False)
        st.session_state["_salvo"] = json.loads(json.dumps(conteudo))
    except Exception:
        pass


def iniciar():
    if "cadastro" not in st.session_state:
        cad, acomp = _ler_arquivo()
        st.session_state.cadastro = cad
        st.session_state["_p_acomp"] = acomp


def adicionar(tickers):
    novos = [t for t in tickers if t not in st.session_state.cadastro]
    st.session_state.cadastro = st.session_state.cadastro + novos
    st.session_state["_p_acomp"] = lembrado("acomp", []) + [t for t in novos if t not in lembrado("acomp", [])]
    st.session_state.pop("w_acomp", None)
    salvar_carteira()
    return novos


def remover(tickers):
    st.session_state.cadastro = [t for t in st.session_state.cadastro if t not in tickers]
    st.session_state["_p_acomp"] = [t for t in lembrado("acomp", []) if t not in tickers]
    st.session_state.pop("w_acomp", None)
    salvar_carteira()


def acompanhando():
    return [t for t in lembrado("acomp", []) if t in st.session_state.cadastro]


def ir_para_empresa(ticker):
    """Callback de botão: abre a página da empresa."""
    if ticker not in lembrado("acomp", []):
        st.session_state["_p_acomp"] = lembrado("acomp", []) + [ticker]
        st.session_state.pop("w_acomp", None)
    definir("nav", "Empresa")
    definir("emp_ticker", ticker)
