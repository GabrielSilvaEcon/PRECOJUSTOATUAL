"""Dashboard personalizável, separado das páginas individuais.
Os filtros só mudam o que é MOSTRADO: nenhum dado original é alterado."""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import estado as est
import filtros
import ui_economia as eco
import valuation as val
from catalogo import CATALOGO, SETORES, mapear_setor
from componentes import cartao
from estilo import COLORWAY, GRID, PLOT
from periodos import anos_completos, ano_parcial_no_periodo

# nome na tela -> (coluna, formato, depende_do_periodo)
METRICAS = {
    "Preço atual": ("Preço", "R$ {:.2f}", False),
    "Preço justo": ("Preço justo", "R$ {:.2f}", False),
    "Margem de segurança (%)": ("Margem (%)", "{:.1f}", False),
    "P/L": ("P/L", "{:.2f}", False),
    "P/VP": ("P/VP", "{:.2f}", False),
    "Dividend yield 12m (%)": ("DY 12m (%)", "{:.2f}", False),
    "ROE (%)": ("ROE (%)", "{:.1f}", False),
    "Margem líquida (%)": ("Margem líq. (%)", "{:.1f}", False),
    "Dívida/PL": ("Dív./PL", "{:.1f}", False),
    "EV/EBITDA": ("EV/EBITDA", "{:.1f}", False),
    "Receita média anual (R$ mi)": ("Receita média (R$ mi)", "{:,.0f}", True),
    "Lucro líquido médio anual (R$ mi)": ("Lucro médio (R$ mi)", "{:,.0f}", True),
    "Fluxo de caixa livre médio (R$ mi)": ("FCL médio (R$ mi)", "{:,.0f}", True),
    "Dividendos médios por ano (R$/ação)": ("Dividendos médios (R$)", "{:.2f}", True),
}
PADRAO_METRICAS = ["Preço atual", "Preço justo", "Margem de segurança (%)", "P/L", "Dividend yield 12m (%)"]
EVOLUCAO = {"Receita": "Receita", "Lucro líquido": "Lucro líquido", "Fluxo de caixa livre": "Fluxo de caixa livre"}


def _linha(tk, d, per, hoje):
    metodo = est.lembrado("val_metodo", "Média (Graham + Bazin)").split(" ")[0]
    r = val.analisar(d, metodo, est.lembrado("val_yield", 6.0), est.lembrado("val_margem", 20))
    mu = val.multiplos(d)
    setor, _ = mapear_setor(tk, d.get("setor_yahoo"), d.get("industria_yahoo"))
    linha = {"Ticker": tk, "Empresa": d["nome"], "Setor": setor or "Não definido", "Preço": d["preco"],
             "Preço justo": r["justo"], "Margem (%)": r["margem"], "P/L": mu["pl"], "P/VP": mu["pvp"],
             "DY 12m (%)": mu["dy"], "ROE (%)": mu["roe"], "Margem líq. (%)": mu["margem"],
             "Dív./PL": d["div_pl"], "EV/EBITDA": d["ev_ebitda"], "_status": r["status"]}
    comp = anos_completos(per, hoje)
    anual = dados.buscar_demonstrativos(tk, "anual")
    sub = anual[anual["Ano"].isin(comp)] if not anual.empty else anual
    linha["_anos_dem"] = list(sub["Ano"]) if not sub.empty else []
    for col_dem, nome in (("Receita", "Receita média (R$ mi)"), ("Lucro líquido", "Lucro médio (R$ mi)"),
                          ("Fluxo de caixa livre", "FCL médio (R$ mi)")):
        ok = not sub.empty and col_dem in sub and sub[col_dem].notna().any()
        linha[nome] = float(sub[col_dem].mean()) / 1e6 if ok else None
    divs = dados.buscar_dividendos(tk)
    usados = [a for a in comp if a in divs.index]
    linha["Dividendos médios (R$)"] = float(divs.loc[usados].mean()) if usados else None
    return linha


def pagina(ativos):
    hoje = datetime.now()
    st.markdown("#### Dashboard")
    st.caption("Monte a sua visão. Os filtros só escondem ou mostram informações; nada é apagado.")

    with st.expander("⚙️ Personalizar o dashboard", expanded=True):
        c1, c2 = st.columns([2, 1.3])
        escolhidas = est.multiselect("dash_emp", "Empresas", ativos, padrao=ativos, onde=c1)
        fontes = est.multiselect("dash_fontes", "Mostrar dados de", ["Ações", "Macroeconomia", "Setores"],
                                 padrao=["Ações"], onde=c2)
        per = filtros.seletor_periodo("per_dash")
        b1, b2, b3, b4 = st.columns(4)
        s_cart = est.checkbox("dash_cart", "Cartões", padrao=True, onde=b1)
        s_graf = est.checkbox("dash_graf", "Gráficos", padrao=True, onde=b2)
        s_tab = est.checkbox("dash_tab", "Tabela", padrao=True, onde=b3)
        s_det = est.checkbox("dash_det", "Botões de detalhe", padrao=True, onde=b4)
        metricas = est.multiselect("dash_met", "Métricas para comparar", list(METRICAS), padrao=PADRAO_METRICAS)

    if "Ações" in fontes:
        _acoes(escolhidas, per, hoje, metricas, s_cart, s_graf, s_tab, s_det)
    if "Macroeconomia" in fontes:
        _macro(per)
    if "Setores" in fontes:
        _setores(per, escolhidas)
    if not fontes:
        st.info("Marque pelo menos uma fonte em “Mostrar dados de”.")
    st.caption("Ferramenta educacional. Indicadores e cenários são modelos simplificados, sem recomendação de investimento.")


def _acoes(escolhidas, per, hoje, metricas, s_cart, s_graf, s_tab, s_det):
    if not escolhidas:
        st.info("Escolha ao menos uma empresa.")
        return
    base = dados.carregar(escolhidas)
    linhas = [_linha(tk, d, per, hoje) for tk, d in base.items()]
    df = pd.DataFrame(linhas)
    if df.empty:
        return
    setores = sorted(df["Setor"].unique())
    filtro = est.multiselect("dash_setor", "Filtrar por setor", setores, padrao=setores)
    df = df[df["Setor"].isin(filtro)]
    if df.empty:
        st.info("Nenhuma empresa no filtro de setor escolhido.")
        return
    if ano_parcial_no_periodo(per, hoje):
        st.caption(f"ℹ️ {ano_parcial_no_periodo(per, hoje)} é parcial: as métricas por período usam só anos completos.")
    dep = [m for m in metricas if METRICAS[m][2]]
    if dep:
        sem = df[df["_anos_dem"].map(len) == 0]["Ticker"].tolist()
        if sem:
            st.warning("Sem demonstrativos de anos completos neste período para: " + ", ".join(sem) +
                       ". As métricas por período aparecem como “—”.")

    st.markdown("##### Empresas")
    if s_cart:
        cols = st.columns(min(len(df), 3))
        for i, (_, row) in enumerate(df.iterrows()):
            with cols[i % len(cols)]:
                r = val.analisar(base[row["Ticker"]], est.lembrado("val_metodo", "Média").split(" ")[0],
                                 est.lembrado("val_yield", 6.0), est.lembrado("val_margem", 20))
                cartao(r)
                if s_det:
                    st.button("Abrir detalhes", key=f"dd_{row['Ticker']}",
                              on_click=est.ir_para_empresa, args=(row["Ticker"],))
    cols_sel = [METRICAS[m][0] for m in metricas]
    if s_graf and cols_sel:
        nome = est.selectbox("dash_grafmet", "Gráfico: comparar por", metricas)
        col = METRICAS[nome][0]
        d2 = df.dropna(subset=[col]).sort_values(col)
        if d2.empty:
            st.info("Sem dados para esta métrica nas empresas escolhidas.")
        else:
            fig = go.Figure(go.Bar(x=d2["Ticker"], y=d2[col], marker_color="#6b7a8f",
                                   text=[f"{v:,.2f}" for v in d2[col]], textposition="outside"))
            fig.update_layout(title=nome, height=320, **PLOT)
            fig.update_yaxes(**GRID)
            st.plotly_chart(fig, width="stretch", key="dash_bar")
            if METRICAS[nome][2]:
                st.caption(f"Média dos anos completos de {per.rotulo} disponíveis para cada empresa.")
        _evolucao(df["Ticker"].tolist(), per, hoje)
    if s_tab and cols_sel:
        tab = df[["Ticker", "Empresa", "Setor"] + cols_sel]
        fmt = {METRICAS[m][0]: METRICAS[m][1] for m in metricas}
        st.dataframe(tab.style.format(fmt, na_rep="—"), width="stretch", hide_index=True)
        st.caption("“—” = dado indisponível na fonte (não é zero). Métricas por período usam só anos completos.")


def _evolucao(tickers, per, hoje):
    comp = anos_completos(per, hoje)
    if len(comp) < 2:
        st.caption("Para ver a evolução ano a ano, escolha um período com pelo menos dois anos completos.")
        return
    nome = est.selectbox("dash_evol", "Evolução anual de", list(EVOLUCAO))
    fig, vazio = go.Figure(), []
    for i, tk in enumerate(tickers):
        a = dados.buscar_demonstrativos(tk, "anual")
        if a.empty or EVOLUCAO[nome] not in a:
            vazio.append(tk)
            continue
        s = a[a["Ano"].isin(comp)].set_index("Ano")[EVOLUCAO[nome]].dropna() / 1e6
        if s.empty:
            vazio.append(tk)
            continue
        fig.add_scatter(x=[str(x) for x in s.index], y=s.values, name=tk, mode="lines+markers",
                        line=dict(color=COLORWAY[i % len(COLORWAY)]))
    if fig.data:
        fig.update_layout(height=320, title=f"{nome} (R$ milhões, anos completos)", **PLOT)
        fig.update_yaxes(**GRID)
        st.plotly_chart(fig, width="stretch", key="dash_evol_fig")
    if vazio:
        st.caption("Sem dados anuais para: " + ", ".join(vazio) + ".")


def _macro(per):
    st.markdown("##### Macroeconomia")
    ids = list(CATALOGO)
    macro_ids = [s.id for s in CATALOGO.values() if s.grupo in
                 ("Juros e inflação", "Câmbio", "Atividade e PIB", "Crédito", "Emprego e renda", "Fiscal")]
    sel = est.multiselect("dash_macro", "Indicadores macroeconômicos", macro_ids,
                          padrao=["selic_meta", "ipca_12m", "dolar"], format_func=lambda i: CATALOGO[i].nome)
    cols = st.columns(3)
    for i, sid in enumerate(sel):
        with cols[i % 3]:
            eco.cartao_serie(sid, per)
    if sel and est.checkbox("dash_macro_graf", "Mostrar gráficos dos indicadores", padrao=False):
        for sid in sel:
            eco.bloco_serie(sid, per, "dash", explicar=False, altura=240)


def _setores(per, escolhidas):
    st.markdown("##### Setores")
    setor = est.selectbox("dash_setor_sel", "Setor", list(SETORES))
    cfg = SETORES[setor]
    sel = est.multiselect(f"dash_set_ind_{setor}", "Indicadores do setor", cfg["indicadores"],
                          padrao=cfg["indicadores"][:3], format_func=lambda i: CATALOGO[i].nome)
    cols = st.columns(3)
    for i, sid in enumerate(sel):
        with cols[i % 3]:
            eco.cartao_serie(sid, per)
            st.caption(cfg["porque"][sid])
    if cfg.get("limitacao"):
        st.caption("Limitação: " + cfg["limitacao"])
