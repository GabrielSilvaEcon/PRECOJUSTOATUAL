"""Seletor de período reutilizável (anos), com escolha lembrada entre abas."""
from datetime import datetime

import streamlit as st

import estado as est
from periodos import OPCOES, Periodo, descrever, resolver


def seletor_periodo(chave: str, label="Período de análise", ano_min=2000, padrao="Últimos 5 anos",
                    ini_padrao=None, fim_padrao=None) -> Periodo:
    hoje = datetime.now()
    anos = list(range(ano_min, hoje.year + 1))
    c1, c2, c3 = st.columns([1.6, 1, 1])
    opcao = est.selectbox(f"{chave}_opc", label, OPCOES, padrao=padrao, onde=c1,
                          help="Anos completos são anos já encerrados. O ano atual é sempre parcial.")
    ini = fim = None
    if opcao == "Intervalo personalizado":
        ini = est.selectbox(f"{chave}_ini", "Ano inicial", anos, padrao=ini_padrao or hoje.year - 4, onde=c2)
        fim = est.selectbox(f"{chave}_fim", "Ano final", anos, padrao=fim_padrao or hoje.year - 1, onde=c3)
        if ini > fim:
            st.warning("O ano inicial é maior que o final; usei os dois em ordem crescente.")
    p = resolver(opcao, ini, fim, hoje)
    if opcao != "Intervalo personalizado":
        c2.caption(f"**{p.rotulo}**")
    st.caption(descrever(p, hoje))
    return p
