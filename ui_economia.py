"""Bloco reutilizável para mostrar UMA série econômica: valor, variações, gráfico, tabela anual,
comparação entre anos, explicação e fonte. Usado em Macroeconomia, Setores, Empresa e Dashboard."""
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

import estado as est
import macro
import macro_core as core
from catalogo import CATALOGO
from estilo import ACCENT, COLORWAY, GRID, PLOT, num
from periodos import Periodo


def carregar_filtrada(sid: str, p: Periodo):
    s = CATALOGO[sid]
    r = macro.carregar_serie(sid)
    df = core.filtrar_anos(r["df"], p.ini, p.fim) if not r["df"].empty else r["df"]
    return s, r, df


def avisos(s, r, df, p: Periodo):
    """Mostra avisos de erro, defasagem e período sem dados. Retorna True se há dados para exibir."""
    if r["erro"]:
        st.warning(f"**{s.nome}** indisponível agora ({s.fonte}). {r['erro']}")
        if s.confianca == "a confirmar":
            st.caption("O código desta série ainda não foi confirmado online; use “Testar fontes” na aba Macroeconomia.")
        return False
    if df.empty:
        total = r["df"]
        st.info(f"**{s.nome}**: a fonte não tem dados entre {p.ini} e {p.fim}. "
                f"Disponível de {total['data'].iloc[0]:%m/%Y} a {total['data'].iloc[-1]:%m/%Y}.")
        return False
    ultima = r["df"]["data"].iloc[-1]
    if core.desatualizada(ultima, s.periodicidade):
        st.caption(f"⚠️ Última observação em {ultima:%d/%m/%Y}: a série pode estar desatualizada.")
    if p.fim >= datetime.now().year:
        st.caption(f"⚠️ {datetime.now().year} é um ano em andamento: valores parciais.")
    return True


def bloco_serie(sid: str, p: Periodo, chave: str, grafico=True, tabela=False, explicar=True,
                comparar=False, relevancia: str = None, altura=280):
    s, r, df = carregar_filtrada(sid, p)
    st.markdown(f"**{s.nome}**")
    if not avisos(s, r, df, p):
        return
    v = core.variacoes(df, s.var)
    c1, c2, c3 = st.columns(3)
    c1.metric("Último valor", f"{num(v['ultimo'], 2)} {s.unidade}", help=f"Referência: {v['data']:%d/%m/%Y}")
    if v["var_anterior"] is not None:
        c2.metric("vs. observação anterior", f"{num(v['var_anterior'], 2)} {v['unidade_var']}")
    if v["var_12m"] is not None:
        c3.metric("vs. 12 meses antes", f"{num(v['var_12m'], 2)} {v['unidade_var']}")
    st.markdown(
        f'<div class="fonte">Fonte: {s.fonte} · Referência: {v["data"]:%d/%m/%Y} · '
        f'Baixado em {r["baixado_em"]:%d/%m/%Y %H:%M} · Período: {p.rotulo} · '
        f'{"Dado oficial" if s.oficial else "Dado de mercado (não oficial)"}</div>', unsafe_allow_html=True)

    if grafico:
        fig = go.Figure(go.Scatter(x=df["data"], y=df["valor"], mode="lines", line=dict(color=ACCENT, width=2)))
        fig.update_layout(height=altura, title=f"{s.nome} ({s.unidade})", **PLOT)
        fig.update_yaxes(**GRID)
        st.plotly_chart(fig, width="stretch", key=f"g_{chave}_{sid}", config={"displaylogo": False})
    if tabela:
        res = core.resumo_anual(df, s.periodicidade)
        st.dataframe(res.style.format({"Média": "{:,.2f}", "Último": "{:,.2f}", "Mínimo": "{:,.2f}",
                                       "Máximo": "{:,.2f}"}, na_rep="—"), width="stretch")
        st.caption("Status por ano: “completo” tem todas as observações esperadas; “incompleto” falta dado na fonte; "
                   "o ano em andamento é sempre parcial. Não compare anos parciais com completos.")
    if comparar:
        anos = sorted(df["data"].dt.year.unique())
        if len(anos) < 2:
            st.caption("Selecione um período com mais de um ano para comparar.")
        else:
            esc = est.multiselect(f"cmp_{chave}_{sid}", "Anos a comparar (mês a mês)", anos, padrao=anos[-2:],
                                  max_selections=5)
            mat = core.sobrepor_anos(df, list(esc)) if esc else None
            if mat is not None and not mat.empty:
                fig2 = go.Figure()
                for i, ano in enumerate(mat.columns):
                    fig2.add_scatter(x=mat.index, y=mat[ano], name=str(ano), mode="lines+markers",
                                     connectgaps=True, line=dict(color=COLORWAY[i % len(COLORWAY)]))
                fig2.update_layout(height=260, xaxis_title="Mês", **PLOT)
                fig2.update_yaxes(**GRID)
                st.plotly_chart(fig2, width="stretch", key=f"c_{chave}_{sid}")
                st.caption("Média por mês de cada ano. Séries trimestrais aparecem só nos meses de fechamento do trimestre.")
    if explicar:
        with st.expander("O que é e por que importa"):
            st.write(s.o_que_e)
            if relevancia:
                st.markdown(f"**Para este setor/empresa:** {relevancia}")
            st.markdown(f"**Em geral:** {s.impacto}")
            st.caption("Os efeitos variam de empresa para empresa; isto é contexto educacional, não uma previsão.")


def cartao_serie(sid: str, p: Periodo):
    """Versão compacta: só os números essenciais, fonte e data."""
    s, r, df = carregar_filtrada(sid, p)
    with st.container(border=True):
        st.markdown(f"**{s.nome}**")
        if r["erro"]:
            st.caption(f"Indisponível agora ({s.fonte}).")
            return
        if df.empty:
            st.caption("Sem dados no período escolhido.")
            return
        v = core.variacoes(df, s.var)
        st.metric("Último valor", f"{num(v['ultimo'], 2)} {s.unidade}",
                  delta=None if v["var_anterior"] is None else f"{num(v['var_anterior'], 2)} {v['unidade_var']}",
                  help="A seta compara com a observação anterior.")
        extra = " · ⚠️ pode estar desatualizada" if core.desatualizada(r["df"]["data"].iloc[-1], s.periodicidade) else ""
        st.markdown(f'<div class="fonte">{s.fonte} · ref. {v["data"]:%d/%m/%Y}{extra}</div>', unsafe_allow_html=True)
