"""Aba Microeconomia e Análise Setorial."""
from datetime import datetime

import streamlit as st

import estado as est
import filtros
import ui_economia as eco
from catalogo import CATALOGO, SETORES, TICKERS_CONHECIDOS


def pagina(ativos):
    st.markdown("#### Microeconomia e análise setorial")
    st.caption("Como indicadores econômicos podem influenciar receitas, custos, margens e riscos de cada setor. "
               "São relações possíveis, não garantias: cada empresa reage de um jeito.")
    hoje = datetime.now()
    setor = est.selectbox("set_setor", "Setor", list(SETORES))
    cfg = SETORES[setor]
    with st.expander("📅 Período e filtros", expanded=True):
        p = filtros.seletor_periodo("per_setor", padrao="Intervalo personalizado",
                                    ini_padrao=hoje.year - 4, fim_padrao=hoje.year)
        c1, c2 = st.columns([2, 1.4])
        ind = est.multiselect(f"set_ind_{setor}", "Indicadores", cfg["indicadores"], padrao=cfg["indicadores"][:3],
                              onde=c1, format_func=lambda i: CATALOGO[i].nome)
        visao = est.selectbox("set_visao", "Visão", ["Visão geral", "Detalhes"], onde=c2)
        o1, o2, o3 = st.columns(3)
        tab = est.checkbox("set_tab", "Tabela anual", padrao=False, onde=o1)
        cmp_ = est.checkbox("set_cmp", "Comparar anos", padrao=False, onde=o2)
        expl = est.checkbox("set_expl", "Explicações", padrao=True, onde=o3)

    cols = st.columns(4)
    for c, (k, txt) in zip(cols, cfg["afeta"].items()):
        c.markdown(f'<div class="card"><div class="lbl">{k}</div><div style="font-size:.85rem">{txt}</div></div>',
                   unsafe_allow_html=True)
    if cfg.get("limitacao"):
        st.caption("Limitação: " + cfg["limitacao"])

    if not ind:
        st.info("Escolha ao menos um indicador.")
    elif visao == "Visão geral":
        cc = st.columns(3)
        for i, sid in enumerate(ind):
            with cc[i % 3]:
                eco.cartao_serie(sid, p)
                st.caption(cfg["porque"][sid])
    else:
        sid = est.selectbox("set_serie", "Indicador em detalhe", ind, format_func=lambda i: CATALOGO[i].nome)
        eco.bloco_serie(sid, p, "set", tabela=tab, comparar=cmp_, explicar=expl, relevancia=cfg["porque"].get(sid), altura=340)

    meus = [t for t in ativos if TICKERS_CONHECIDOS.get(t) == setor]
    if meus:
        st.markdown("**Suas ações neste setor** (mapeamento interno; confirme na página da empresa)")
        bc = st.columns(min(len(meus), 6))
        for c, t in zip(bc, meus):
            c.button(t, key=f"set_ab_{t}", on_click=est.ir_para_empresa, args=(t,))
