"""Página individual da empresa: Resumo · Fundamentalista · Valuation · Técnica · Contexto econômico."""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import estado as est
import filtros
import tecnica_ui
import ui_economia as eco
import valuation as val
from catalogo import (JUSTIFICATIVA_GERAL, JUSTIFICATIVA_SETOR, JUSTIFICATIVA_YIELD, SETORES, mapear_setor)
from componentes import cartao, gauge
from estilo import BAD, COLORWAY, ETIQUETAS, GOOD, GRID, MUTED, PLOT, brl, num
from periodos import (anos_completos, anos_faltantes, ano_parcial_no_periodo, filtrar_por_ano, rotulo_trimestre)

SECOES = ["Resumo", "Fundamentalista", "Valuation", "Técnica", "Contexto econômico"]
AJUDA = {
    "P/L": "Preço ÷ lucro por ação. Quantos anos de lucro atual o preço representa.",
    "P/VP": "Preço ÷ valor patrimonial por ação. Abaixo de 1 = preço menor que o patrimônio contábil.",
    "DY 12m": "Dividend yield: proventos dos últimos 12 meses ÷ preço.",
    "ROE": "Retorno sobre o patrimônio: quanto a empresa lucra para cada R$ 100 de patrimônio.",
    "Margem líquida": "Quanto sobra de lucro para cada R$ 100 de receita.",
    "Dív./PL": "Dívida ÷ patrimônio líquido, como informado pelo Yahoo Finance.",
    "EV/EBITDA": "Valor da empresa ÷ geração operacional de caixa (EBITDA).",
}


def pagina(ativos):
    c1, _ = st.columns([1, 3])
    tk = est.selectbox("emp_ticker", "Empresa", ativos, onde=c1)
    try:
        d = dados.buscar(tk)
    except Exception as e:
        st.error(f"Não consegui carregar {tk}: {e}")
        return
    st.markdown(f'<div class="tk">{tk} <span class="sub">· {d["nome"]}</span></div>', unsafe_allow_html=True)

    with st.expander("📅 Anos analisados (vale para as seções abaixo)", expanded=False):
        per = filtros.seletor_periodo(f"per_{tk}")
    sec = est.segmentado("emp_sec", "Seção", SECOES)

    if sec == "Resumo":
        resumo(tk, d)
    elif sec == "Fundamentalista":
        fundamentalista(tk, d, per)
    elif sec == "Valuation":
        valuation(tk, d, per)
    elif sec == "Técnica":
        tecnica_ui.pagina(tk, per)
    else:
        contexto(tk, d, per)


# ---------------------------------------------------------------- resumo
def resumo(tk, d):
    metodo = est.lembrado("val_metodo", "Média (Graham + Bazin)")
    y = est.lembrado("val_yield", 6.0)
    m = est.lembrado("val_margem", 20)
    r = val.analisar(d, metodo.split(" ")[0], y, m)
    a, b = st.columns([1, 1])
    with a:
        cartao(r)
        st.plotly_chart(gauge(r["margem"]), width="stretch", key=f"g_res_{tk}", config={"displayModeBar": False})
        st.caption("Margem de segurança = quanto o preço atual está abaixo do preço justo estimado. "
                   "Veja as premissas na seção Valuation.")
    with b:
        mu = val.multiplos(d)
        x1, x2 = st.columns(2)
        x1.metric("P/L", num(mu["pl"]), help=AJUDA["P/L"])
        x2.metric("P/VP", num(mu["pvp"]), help=AJUDA["P/VP"])
        x1.metric("DY 12m", num(mu["dy"], 2, "%"), help=AJUDA["DY 12m"])
        x2.metric("ROE", num(mu["roe"], 1, "%"), help=AJUDA["ROE"])
        st.caption("Indicadores atuais (não dependem do filtro de anos). Fonte: Yahoo Finance; podem estar defasados.")
    st.button("Ver análise técnica →", key=f"bt_{tk}", on_click=est.definir, args=("emp_sec", "Técnica"))


# ---------------------------------------------------------------- fundamentalista
def fundamentalista(tk, d, per):
    hoje = datetime.now()
    mu = val.multiplos(d)
    st.markdown("#### Indicadores atuais")
    cols = st.columns(4)
    itens = [("P/L", mu["pl"], ""), ("P/VP", mu["pvp"], ""), ("DY 12m", mu["dy"], "%"), ("ROE", mu["roe"], "%"),
             ("Margem líquida", mu["margem"], "%"), ("EV/EBITDA", d["ev_ebitda"], ""), ("Dív./PL", d["div_pl"], "")]
    for i, (nome, v, suf) in enumerate(itens):
        cols[i % 4].metric(nome, num(v, 2, suf), help=AJUDA[nome])
    st.caption("Estes valores são do momento atual e não mudam com o filtro de anos.")

    st.markdown("#### Resultados por período")
    c1, c2 = st.columns([1.3, 2])
    visao = est.selectbox(f"vis_{tk}", "Visão", ["Anual (anos completos)", "Trimestral"], onde=c1)
    moeda = d["moeda"]
    if moeda != "BRL":
        st.caption(f"Valores na moeda do balanço ({moeda}).")
    if visao.startswith("Anual"):
        _anual(tk, per, c2, hoje)
    else:
        _trimestral(tk, per, hoje)

    st.markdown("#### Dividendos por ação")
    divs = dados.buscar_dividendos(tk)
    if divs.empty:
        st.info("Sem histórico de dividendos para este ativo.")
        return
    dd = filtrar_por_ano(divs, per, incluir_parcial=True, hoje=hoje)
    if dd.empty:
        st.info("Não há dividendos registrados nos anos selecionados.")
        return
    parc = ano_parcial_no_periodo(per, hoje)
    rot = [f"{a} (parcial)" if a == parc else str(a) for a in dd.index]
    fig = go.Figure(go.Bar(x=rot, y=dd.values, marker_color=["#c2ad7e" if a == parc else "#6b7a8f" for a in dd.index]))
    fig.update_layout(height=300, title="R$ por ação", **PLOT)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, width="stretch", key=f"dv_{tk}")
    miss = anos_faltantes(divs.index, anos_completos(per, hoje))
    if miss:
        st.caption(f"Sem proventos registrados em: {', '.join(map(str, miss))}.")
    if parc:
        st.caption(f"{parc} está em andamento: não compare com anos completos.")


def _anual(tk, per, col, hoje):
    df = dados.buscar_demonstrativos(tk, "anual")
    if df.empty:
        st.info("O Yahoo Finance não retornou demonstrativos anuais para este ativo.")
        return
    comp = anos_completos(per, hoje)
    sub = df[df["Ano"].isin(comp)].copy()
    sub.index = sub["Ano"]
    sub = sub.drop(columns="Ano")
    falt = anos_faltantes(sub.index, comp)
    if falt:
        st.warning(f"Sem demonstrativo anual para: {', '.join(map(str, falt))}. "
                   f"Anos disponíveis na fonte: {', '.join(map(str, sorted(df['Ano'].unique())))}.")
    parc = ano_parcial_no_periodo(per, hoje)
    linhas_parc = None
    if parc:
        st.info(f"{parc} ainda não terminou, então não existe demonstrativo anual. "
                "Use a visão Trimestral ou ative o acumulado parcial abaixo.")
        if est.checkbox(f"parcial_{tk}", f"Mostrar acumulado parcial de {parc} (soma dos trimestres divulgados)",
                        padrao=False, onde=col):
            q = dados.buscar_demonstrativos(tk, "trimestral")
            q = q[q["Ano"] == parc] if not q.empty else q
            if q.empty:
                st.caption(f"Nenhum trimestre de {parc} divulgado ainda.")
            else:
                soma = q.drop(columns="Ano").sum(min_count=1)
                linhas_parc = (f"{parc} (parcial: {len(q)} tri)", soma)
    if sub.empty and linhas_parc is None:
        return
    tabela = (sub.sort_index() / 1e6)
    if linhas_parc:
        tabela.loc[linhas_parc[0]] = linhas_parc[1] / 1e6
    tabela.index = [str(i) for i in tabela.index]
    _grafico_resultados(tabela, f"an_{tk}", "R$ milhões por ano")
    st.dataframe(tabela.T.style.format("{:,.0f}", na_rep="—"), width="stretch")


def _trimestral(tk, per, hoje):
    df = dados.buscar_demonstrativos(tk, "trimestral")
    if df.empty:
        st.info("O Yahoo Finance não retornou demonstrativos trimestrais para este ativo.")
        return
    sub = df[(df["Ano"] >= per.ini) & (df["Ano"] <= per.fim)]
    if sub.empty:
        st.warning("Sem trimestres divulgados nos anos selecionados. "
                   f"Disponível na fonte: {rotulo_trimestre(df.index[0])} a {rotulo_trimestre(df.index[-1])}.")
        return
    tabela = sub.drop(columns="Ano") / 1e6
    tabela.index = [rotulo_trimestre(i) for i in tabela.index]
    _grafico_resultados(tabela, f"tr_{tk}", "R$ milhões por trimestre")
    st.dataframe(tabela.T.style.format("{:,.0f}", na_rep="—"), width="stretch")
    st.caption("Trimestres não somam um ano completo se faltar algum. A fonte entrega só os trimestres mais recentes.")


def _grafico_resultados(tabela, chave, titulo):
    fig = go.Figure()
    for i, col in enumerate([c for c in ("Receita", "Lucro líquido", "Fluxo de caixa livre") if c in tabela]):
        fig.add_bar(x=list(tabela.index), y=tabela[col], name=col, marker_color=COLORWAY[i])
    if not fig.data:
        st.info("Receita, lucro e fluxo de caixa não estão disponíveis para este ativo.")
        return
    fig.update_layout(barmode="group", height=320, title=titulo, legend=dict(orientation="h", y=1.15), **PLOT)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, width="stretch", key=f"res_{chave}")


# ---------------------------------------------------------------- valuation
def valuation(tk, d, per):
    hoje = datetime.now()
    c1, c2, c3 = st.columns(3)
    metodo = est.selectbox("val_metodo", "Método", ["Média (Graham + Bazin)", "Graham", "Bazin"], onde=c1)
    yield_alvo = est.slider("val_yield", "Dividend yield desejado (Bazin)", 4.0, 12.0, 6.0, 0.5, onde=c2, format="%.1f%%")
    margem_alvo = est.slider("val_margem", "Margem de segurança alvo", 5, 50, 20, 5, onde=c3, format="%d%%")

    base_hist = est.selectbox("val_hist", "Histórico usado em Bazin e DCF",
                              ["Padrão: 5 anos de dividendos e 3 de fluxo de caixa", "Anos do período selecionado"])
    divs = dados.buscar_dividendos(tk)
    caixa = dados.buscar_caixa(tk)
    d2, n_fcl, caixa_uso, anos_div, anos_fcl = dict(d), 3, caixa, [], []
    if base_hist.startswith("Anos"):
        media, anos_div = val.div_medio_periodo(divs, per, hoje)
        d2["div_medio"] = media
        caixa_uso, anos_fcl = val.caixa_periodo(caixa, per, hoje)
        n_fcl = max(len(anos_fcl), 1)
        if ano_parcial_no_periodo(per, hoje):
            st.info(f"{ano_parcial_no_periodo(per, hoje)} é parcial e foi ignorado nos cálculos.")
        if not anos_div:
            st.warning("Sem dividendos em anos completos do período: Bazin indisponível.")
        if not anos_fcl:
            st.warning("Sem fluxo de caixa em anos completos do período: DCF indisponível.")
    else:
        anos_div = list(d["div_ano"].index)
        anos_fcl = list(caixa["Fluxo de caixa livre"].dropna().tail(3).index) if "Fluxo de caixa livre" in caixa else []

    r = val.analisar(d2, metodo.split(" ")[0], yield_alvo, margem_alvo)
    a, b = st.columns([1, 1.4])
    with a:
        cartao(r)
        st.plotly_chart(gauge(r["margem"]), width="stretch", key=f"g_val_{tk}", config={"displayModeBar": False})
    with b:
        st.markdown("**Premissas do DCF**")
        e1, e2, e3 = st.columns(3)
        taxa = est.slider("dcf_taxa", "Taxa de desconto", 8.0, 20.0, 12.0, 0.5, onde=e1, format="%.1f%%") / 100
        g = est.slider("dcf_g", "Crescimento do FCL (5 anos)", -5.0, 15.0, 4.0, 0.5, onde=e2, format="%.1f%%") / 100
        gp = est.slider("dcf_gp", "Crescimento na perpetuidade", 0.0, 5.0, 3.0, 0.5, onde=e3, format="%.1f%%") / 100
        v_dcf, base_fcl = val.dcf(caixa_uso, d["acoes"], d["moeda"], taxa, g, gp, n_anos=n_fcl)
        marg_dcf = (v_dcf - d["preco"]) / v_dcf * 100 if v_dcf and d["preco"] else None
        tab = pd.DataFrame([
            {"Método": "Graham", "Valor por ação": r["graham"], "Base": f"LPA {num(d['lpa'])} · VPA {num(d['vpa'])} (atuais)"},
            {"Método": "Bazin", "Valor por ação": r["bazin"],
             "Base": f"dividendo médio {brl(d2['div_medio'])} · anos {_anos(anos_div)}"},
            {"Método": "DCF", "Valor por ação": v_dcf,
             "Base": f"FCL médio {num(base_fcl / 1e6 if base_fcl is not None and not pd.isna(base_fcl) else None, 0)} mi · anos {_anos(anos_fcl)}"},
        ])
        st.dataframe(tab.style.format({"Valor por ação": "R$ {:.2f}"}, na_rep="—"), width="stretch", hide_index=True)
        if marg_dcf is not None:
            st.caption(f"Margem de segurança pelo DCF: {marg_dcf:.1f}%")

    with st.expander("Como foi calculado e quais são as limitações"):
        st.markdown(
            "- **Graham** = √(22,5 × LPA × VPA). Usa LPA e VPA *atuais*; o filtro de anos não se aplica.\n"
            "- **Bazin** = dividendo médio por ação ÷ yield desejado. Usa apenas **anos completos**.\n"
            "- **DCF** = valor presente de 5 anos de fluxo de caixa livre (FCL) mais valor na perpetuidade, ÷ nº de ações. "
            "Usa a média do FCL dos anos escolhidos, sem ajustar dívida líquida. Não é adequado para bancos e holdings, "
            "e fica em branco se o FCL for negativo, o balanço não estiver em reais ou a taxa for ≤ perpetuidade.")
        if d["moeda"] != "BRL":
            st.warning(f"Balanço em {d['moeda']}: LPA/VPA e DCF podem não estar em reais.")
    cenarios(tk, d2, caixa_uso, n_fcl, metodo.split(" ")[0], yield_alvo, taxa * 100, g * 100, gp * 100)


def _anos(lst):
    return ", ".join(str(a) for a in lst) if lst else "—"


def cenarios(tk, d, caixa, n_fcl, metodo, yield_alvo, taxa, g, gp):
    st.markdown("#### Simulação de cenários (economia e setor)")
    st.markdown(ETIQUETAS, unsafe_allow_html=True)
    st.caption("O cenário **Base** é exatamente o cálculo acima. Pessimista e otimista aplicam as variações que "
               "VOCÊ define na tabela; elas são **estimativas ilustrativas**, não previsões, e não alteram o preço justo "
               "mostrado acima.")
    sug, origem = mapear_setor(tk, d.get("setor_yahoo"), d.get("industria_yahoo"))
    setores = list(SETORES)
    setor = est.selectbox(f"setor_{tk}", "Setor (define a justificativa econômica)", ["Não definido"] + setores,
                          padrao=sug or "Não definido")
    just_setor = JUSTIFICATIVA_SETOR.get(setor, {})
    nomes = {k: n for k, n, _ in val.ALAVANCAS}
    just = {"taxa": JUSTIFICATIVA_GERAL["taxa"], "yield": JUSTIFICATIVA_YIELD, **just_setor}

    ref = _selic_ref()
    if ref:
        st.markdown(f'<span class="etq etq-of">Dado oficial</span> Meta Selic em {ref[1]:%d/%m/%Y}: **{ref[0]:.2f}% a.a.** '
                    '(Banco Central). Referência para pensar na taxa de desconto; o app não a aplica sozinho.',
                    unsafe_allow_html=True)

    linhas = []
    for k, n, metodo_usa in val.ALAVANCAS:
        linhas.append({"Alavanca": n, "Afeta": metodo_usa, "Pessimista": val.DELTAS_PADRAO["Pessimista"][k],
                       "Base": 0.0, "Otimista": val.DELTAS_PADRAO["Otimista"][k],
                       "Justificativa econômica": just.get(k, "Sem vínculo econômico direto mapeado: use com cautela.")})
    ed = st.data_editor(pd.DataFrame(linhas), hide_index=True, width="stretch", key=f"ed_cen_{tk}",
                        disabled=["Alavanca", "Afeta", "Base", "Justificativa econômica"])
    base = dict(yield_alvo=yield_alvo, taxa=taxa, g=g, gp=gp, n_fcl=n_fcl)
    res = {}
    for nome in val.CENARIOS:
        delta = {k: float(pd.to_numeric(ed.loc[i, nome], errors="coerce") if pd.notna(ed.loc[i, nome]) else 0.0)
                 for i, (k, _, _) in enumerate(val.ALAVANCAS)}
        res[nome] = val.calcular_cenario(d, caixa, base, delta, metodo)
    tab = pd.DataFrame({nome: {"Graham": r["graham"], "Bazin": r["bazin"], "DCF": r["dcf"],
                               f"Preço justo ({metodo})": r["justo"], "Margem de segurança (%)": r["margem"]}
                        for nome, r in res.items()})
    fmt = {n: "{:.2f}" for n in val.CENARIOS}
    st.dataframe(tab.style.format(fmt, na_rep="—"), width="stretch")
    with st.expander("Contas de cada cenário"):
        for nome, r in res.items():
            st.markdown(f"**{nome}**")
            for ln in r["linhas"]:
                st.write("• " + ln)
    st.caption("Dados oficiais = séries do Banco Central/IBGE. Interpretação = a justificativa de cada alavanca. "
               "Estimativa = os percentuais da tabela, editáveis por você.")


def _selic_ref():
    try:
        import macro
        r = macro.carregar_serie("selic_meta")
        if r["erro"] or r["df"].empty:
            return None
        u = r["df"].iloc[-1]
        return float(u["valor"]), u["data"]
    except Exception:
        return None


# ---------------------------------------------------------------- contexto econômico
def contexto(tk, d, per):
    sug, origem = mapear_setor(tk, d.get("setor_yahoo"), d.get("industria_yahoo"))
    setor = est.selectbox(f"setor_{tk}", "Setor para análise", ["Não definido"] + list(SETORES),
                          padrao=sug or "Não definido")
    if setor == "Não definido":
        st.info("Não consegui identificar o setor desta empresa. Escolha um setor acima para ver os indicadores relacionados.")
        return
    st.caption(f"Sugestão automática: {sug or 'nenhuma'} ({origem}). Confirme: empresas diversificadas podem ter mais de um setor.")
    cfg = SETORES[setor]
    cols = st.columns(4)
    for c, (k, txt) in zip(cols, cfg["afeta"].items()):
        c.markdown(f'<div class="card"><div class="lbl">{k}</div><div style="font-size:.85rem">{txt}</div></div>',
                   unsafe_allow_html=True)
    st.caption("São canais possíveis de influência, não efeitos garantidos: o impacto muda de empresa para empresa.")
    if cfg.get("limitacao"):
        st.caption("Limitação: " + cfg["limitacao"])
    escolhidos = est.multiselect(f"ctx_ind_{tk}", "Indicadores a mostrar", cfg["indicadores"],
                                 padrao=cfg["indicadores"][:2],
                                 format_func=lambda i: eco.CATALOGO[i].nome)
    for sid in escolhidos:
        with st.container(border=True):
            eco.bloco_serie(sid, per, f"emp_{tk}", relevancia=cfg["porque"].get(sid), comparar=True)
