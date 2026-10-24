"""
Painel B3 – Fundamentalista, Valuation, Técnica, Macroeconomia e Análise Setorial
Rodar com:  streamlit run app.py
Dependências: pip install -r requirements.txt
"""
from datetime import datetime

import streamlit as st

import dados
import estado as est
import estilo

st.set_page_config(page_title="Painel B3", page_icon="📈", layout="wide")
estilo.aplicar()
est.iniciar()

# ---------------------------------------------------------------- sidebar: cadastro de ações
with st.sidebar:
    st.markdown("### Minhas ações")
    with st.form("add", clear_on_submit=True):
        novo = st.text_input("Adicionar por ticker", placeholder="Ex.: WEGE3, TAEE11")
        sem_validar = st.checkbox("Adicionar sem validar (sem internet)")
        enviado = st.form_submit_button("Adicionar", width="stretch")
    if enviado:
        brutos = [dados.normaliza(t) for t in novo.replace(";", ",").replace(" ", ",").split(",") if t.strip()]
        aceitos, msgs = [], []
        for t in brutos:
            if t in st.session_state.cadastro:
                msgs.append(f"{t} já está na lista.")
            elif not dados.PADRAO_TICKER.match(t):
                msgs.append(f"“{t}” não parece um ticker da B3 (ex.: PETR4).")
            elif sem_validar or dados.validar_ticker(t):
                aceitos.append(t)
            else:
                msgs.append(f"Não encontrei cotação para {t}. Confira o ticker ou marque “sem validar”.")
        if aceitos:
            est.adicionar(aceitos)
            msgs.append("Adicionado: " + ", ".join(aceitos))
        st.session_state["msg_cadastro"] = msgs
    for m in st.session_state.pop("msg_cadastro", []):
        st.caption(m)

    with st.expander("Pesquisar por nome"):
        q = st.text_input("Nome da empresa", key="busca_nome", placeholder="Ex.: Weg")
        if st.button("Pesquisar", key="btn_busca") and q.strip():
            st.session_state["achados"] = dados.pesquisar_nome(q.strip())
            st.session_state["achados_q"] = q.strip()
        for i, a in enumerate(st.session_state.get("achados", [])):
            ja = a["ticker"] in st.session_state.cadastro
            st.button(f"{'✓' if ja else '+'} {a['ticker']} · {a['nome'][:22]}", key=f"ach_{i}", disabled=ja,
                      on_click=est.adicionar, args=([a["ticker"]],), width="stretch")
        if st.session_state.get("achados_q") and not st.session_state.get("achados"):
            st.caption("Nada encontrado (ou a busca está indisponível). Você pode digitar o ticker diretamente.")

    acomp = est.multiselect("acomp", "Acompanhando", st.session_state.cadastro, padrao=st.session_state.cadastro)
    est.salvar_carteira()
    with st.expander("Remover da lista"):
        rem = st.multiselect("Tickers a remover", st.session_state.cadastro, key="rem_sel")
        if st.button("Remover selecionados", width="stretch", disabled=not rem):
            est.remover(rem)
            st.session_state.pop("rem_sel", None)
            st.rerun()
    if st.button("Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Fontes: Yahoo Finance (cotações e balanços), TradingView (gráfico), Banco Central e IBGE (economia).")

# ---------------------------------------------------------------- cabeçalho e navegação
st.markdown(
    f'<div class="topo"><span class="hero">Painel B3</span>'
    f'<span class="sub">Atualizado em {datetime.now():%d/%m/%Y %H:%M}</span></div>',
    unsafe_allow_html=True,
)
PAGINAS = ["Dashboard", "Empresa", "Comparar ações", "Macroeconomia", "Setores"]
nav = est.segmentado("nav", "Navegação", PAGINAS)

ativos = est.acompanhando()
precisa_ativos = nav in ("Dashboard", "Empresa", "Comparar ações")
if precisa_ativos and not ativos:
    st.info("Adicione ou marque um ticker na barra lateral para começar.")
    st.stop()

if nav == "Dashboard":
    import pagina_dashboard
    pagina_dashboard.pagina(ativos)
elif nav == "Empresa":
    import pagina_empresa
    pagina_empresa.pagina(ativos)
elif nav == "Comparar ações":
    import pagina_comparar
    pagina_comparar.pagina(ativos)
elif nav == "Macroeconomia":
    import pagina_macro
    pagina_macro.pagina()
else:
    import pagina_setores
    pagina_setores.pagina(ativos)

st.caption("Ferramenta educacional. Graham, Bazin, DCF, cenários e sinais técnicos são modelos simplificados "
           "e não são recomendação de investimento.")
