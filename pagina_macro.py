"""Aba Macroeconomia: indicadores oficiais (Banco Central, IBGE) com período, fonte e explicações."""
from datetime import datetime

import streamlit as st

import estado as est
import filtros
import macro
import ui_economia as eco
from catalogo import CATALOGO, GRUPOS_MACRO


def pagina():
    st.markdown("#### Macroeconomia")
    st.caption("Indicadores que formam o cenário em que as empresas operam. "
               "Dados do Banco Central e do IBGE, sem chave de acesso.")
    hoje = datetime.now()
    with st.expander("📅 Período e filtros", expanded=True):
        p = filtros.seletor_periodo("per_macro", padrao="Intervalo personalizado",
                                    ini_padrao=hoje.year - 4, fim_padrao=hoje.year)
        c1, c2 = st.columns([2, 1.4])
        grupos = est.multiselect("macro_grupos", "Grupos de indicadores", GRUPOS_MACRO,
                                 padrao=["Juros e inflação", "Câmbio"], onde=c1)
        visao = est.selectbox("macro_visao", "Visão", ["Visão geral", "Detalhes"], onde=c2)
        o1, o2, o3, o4 = st.columns(4)
        graf = est.checkbox("macro_graf", "Gráficos", padrao=True, onde=o1)
        tab = est.checkbox("macro_tab", "Tabela anual", padrao=False, onde=o2)
        cmp_ = est.checkbox("macro_cmp", "Comparar anos", padrao=False, onde=o3)
        expl = est.checkbox("macro_expl", "Explicações", padrao=True, onde=o4)

    ids = [s.id for s in CATALOGO.values() if s.grupo in grupos]
    if not ids:
        st.info("Escolha ao menos um grupo de indicadores.")
    elif visao == "Visão geral":
        cols = st.columns(3)
        for i, sid in enumerate(ids):
            with cols[i % 3]:
                eco.cartao_serie(sid, p)
        st.caption("Troque para “Detalhes” para ver gráficos, tabelas anuais e explicações.")
    else:
        sid = est.selectbox("macro_serie", "Indicador", ids, format_func=lambda i: CATALOGO[i].nome)
        eco.bloco_serie(sid, p, "macro", grafico=graf, tabela=tab, explicar=expl, comparar=cmp_, altura=340)

    st.divider()
    with st.expander("Fontes, atualização e como configurar"):
        st.markdown(
            "- **Banco Central do Brasil (SGS)**: API aberta, sem cadastro. Selic, IPCA, câmbio, crédito, inadimplência, "
            "dívida pública e atividade (IBC-Br).\n"
            "- **IBGE (SIDRA)**: API aberta, sem cadastro. PIB, renda, produção industrial e vendas do varejo.\n"
            "- **Tesouro Nacional**: ainda **não integrado** diretamente. Os dados fiscais mostrados vêm do Banco Central.\n"
            "- **Yahoo Finance**: usado só para o petróleo Brent (dado de mercado, não oficial).\n\n"
            "Os dados ficam em cache por 1 hora. Cada gráfico mostra fonte, data de referência e horário do download. "
            "Quando uma fonte falha, o app avisa e **não preenche com zero**.")
        if st.button("Atualizar dados econômicos"):
            macro._serie_cache.clear()
            st.rerun()
    with st.expander("Testar fontes (diagnóstico)"):
        st.caption("Consulta cada série e mostra se funcionou. Códigos marcados como “a confirmar” ainda não foram testados online.")
        if st.button("Rodar teste agora"):
            barra = st.progress(0.0)
            tabela = macro.diagnosticar(progresso=barra.progress)
            st.session_state["diagnostico"] = tabela
            barra.empty()
        if "diagnostico" in st.session_state:
            st.dataframe(st.session_state["diagnostico"], width="stretch", hide_index=True)
