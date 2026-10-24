"""Comparar ações: as quatro seções do app original (Valuation, Fluxo de caixa, Preço justo, Dividendos),
preservadas, agora com filtro de anos nas seções históricas (Fluxo de caixa e Dividendos)."""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import estado as est
import filtros
import valuation as val
from componentes import cartao, gauge, margem_cor
from estilo import BAD, COLORWAY, FAIR, GOOD, GRID, PLOT, brl
from periodos import ano_parcial_no_periodo, anos_completos, anos_faltantes, filtrar_por_ano

SECOES = ["Valuation", "Fluxo de caixa", "Preço justo", "Dividendos"]


def pagina(ativos):
    d = dados.carregar(ativos)
    if not d:
        return
    sec = est.segmentado("cmp_sec", "Seção", SECOES)
    if sec in ("Fluxo de caixa", "Dividendos"):
        with st.expander("📅 Anos analisados", expanded=False):
            per = filtros.seletor_periodo("per_comparar")
    else:
        per = None
    if sec == "Valuation":
        pagina_valuation(d)
    elif sec == "Preço justo":
        pagina_preco_justo(d)
    elif sec == "Fluxo de caixa":
        pagina_caixa(d, per)
    else:
        pagina_dividendos(d, per)


def pagina_preco_justo(dados_):
    c1, c2, c3 = st.columns(3)
    metodo = est.selectbox("val_metodo", "Método", ["Média (Graham + Bazin)", "Graham", "Bazin"], onde=c1)
    yield_alvo = est.slider("val_yield", "Dividend yield desejado (Bazin)", 4.0, 12.0, 6.0, 0.5, onde=c2, format="%.1f%%")
    margem_alvo = est.slider("val_margem", "Margem de segurança alvo", 5, 50, 20, 5, onde=c3, format="%d%%")
    st.caption("Graham = √(22,5 × LPA × VPA)  ·  Bazin = dividendo médio de 5 anos ÷ yield desejado. "
               "Para escolher outros anos de dividendos, use a página da empresa.")

    resultados = [val.analisar(d, metodo.split(" ")[0], yield_alvo, margem_alvo) for d in dados_.values()]
    t_painel, t_comp = st.tabs(["Painel", "Comparativo"])

    with t_painel:
        por_linha = 3
        for i in range(0, len(resultados), por_linha):
            cols = st.columns(por_linha)
            for col, r in zip(cols, resultados[i:i + por_linha]):
                with col:
                    cartao(r)
                    st.plotly_chart(gauge(r["margem"]), width="stretch",
                                    key=f"g_{r['ticker']}", config={"displayModeBar": False})
                    st.caption(f"Margem de segurança · Graham {brl(r['graham'])} · Bazin {brl(r['bazin'])}")
                    st.button("Abrir página da empresa", key=f"ab_{r['ticker']}",
                              on_click=est.ir_para_empresa, args=(r["ticker"],))

    with t_comp:
        df = pd.DataFrame([{
            "Ticker": r["ticker"], "Preço": r["preco"], "Preço justo": r["justo"],
            "Margem (%)": r["margem"], "Status": r["status"],
        } for r in resultados])

        fig = go.Figure()
        fig.add_bar(x=df["Ticker"], y=df["Preço"], name="Preço atual", marker_color="#6b7a8f")
        fig.add_bar(x=df["Ticker"], y=df["Preço justo"], name="Preço justo", marker_color="#7fae93")
        fig.update_layout(barmode="group", height=340, legend=dict(orientation="h", y=1.1), **PLOT)
        fig.update_yaxes(**GRID)
        st.plotly_chart(fig, width="stretch")

        d2 = df.dropna(subset=["Margem (%)"]).sort_values("Margem (%)")
        if not d2.empty:
            fig2 = go.Figure(go.Bar(
                x=d2["Margem (%)"], y=d2["Ticker"], orientation="h",
                marker_color=[margem_cor(m, margem_alvo) for m in d2["Margem (%)"]],
                text=[f"{m:.1f}%" for m in d2["Margem (%)"]], textposition="outside"))
            fig2.update_layout(title="Margem de segurança", height=90 + 46 * len(d2), **PLOT)
            fig2.update_xaxes(**GRID)
            st.plotly_chart(fig2, width="stretch")

        st.dataframe(df.style.format({"Preço": "R$ {:.2f}", "Preço justo": "R$ {:.2f}",
                                      "Margem (%)": "{:.1f}%"}, na_rep="—"),
                     width="stretch", hide_index=True)


def pagina_valuation(dados_):
    linhas = []
    for tk, d in dados_.items():
        m = val.multiplos(d)
        linhas.append({
            "Ticker": tk, "Preço": d["preco"], "P/L": m["pl"], "P/VP": m["pvp"],
            "EV/EBITDA": d["ev_ebitda"], "DY 12m (%)": m["dy"], "ROE (%)": m["roe"],
            "Margem líq. (%)": m["margem"], "Dív./PL (%)": d["div_pl"],
        })
    df = pd.DataFrame(linhas)
    metricas = [c for c in df.columns if c not in ("Ticker", "Preço")]
    metrica = est.selectbox("cmp_metrica", "Comparar por", metricas)

    d2 = df.dropna(subset=[metrica]).sort_values(metrica)
    if d2.empty:
        st.info("Sem dados disponíveis para esse indicador nos ativos selecionados.")
    else:
        fig = go.Figure(go.Bar(x=d2["Ticker"], y=d2[metrica], marker_color="#6b7a8f",
                               text=[f"{v:.2f}" for v in d2[metrica]], textposition="outside"))
        fig.update_layout(title=metrica, height=340, **PLOT)
        fig.update_yaxes(**GRID)
        st.plotly_chart(fig, width="stretch")

    st.dataframe(df.style.format({c: "{:.2f}" for c in df.columns if c != "Ticker"}, na_rep="—"),
                 width="stretch", hide_index=True)
    st.caption("P/L = preço ÷ LPA · P/VP = preço ÷ VPA · DY 12m = proventos dos últimos 12 meses ÷ preço. "
               "Indicadores de balanço vêm do Yahoo Finance e podem estar defasados. Não dependem do filtro de anos.")


def pagina_caixa(dados_, per):
    hoje = datetime.now()
    st.markdown("#### Fluxo de caixa histórico")
    tk = est.selectbox("cx_ativo", "Ativo", list(dados_))
    caixa = dados.buscar_caixa(tk)
    if caixa.empty:
        st.info(f"Sem dados de fluxo de caixa para {tk}.")
    else:
        sub = filtrar_por_ano(caixa, per, incluir_parcial=False, hoje=hoje)
        falt = anos_faltantes(sub.index, anos_completos(per, hoje))
        if ano_parcial_no_periodo(per, hoje):
            st.caption(f"{ano_parcial_no_periodo(per, hoje)} está em andamento e não entra: o fluxo de caixa anual só existe para anos completos.")
        if falt:
            st.warning(f"Sem fluxo de caixa para: {', '.join(map(str, falt))}. "
                       f"Disponível na fonte: {', '.join(map(str, caixa.index))}.")
        if sub.empty:
            st.info("Nenhum ano completo disponível no período escolhido.")
        else:
            cores = {"Caixa operacional": "#6b7a8f", "Capex": "#c08580", "Fluxo de caixa livre": "#7fae93"}
            fig = go.Figure()
            for col in sub.columns:
                fig.add_bar(x=[str(a) for a in sub.index], y=sub[col] / 1e6, name=col, marker_color=cores.get(col))
            fig.update_layout(barmode="group", height=340, title="R$ milhões por ano",
                              legend=dict(orientation="h", y=1.12), **PLOT)
            fig.update_yaxes(**GRID)
            st.plotly_chart(fig, width="stretch")
            st.dataframe((sub / 1e6).T.style.format("{:,.0f}", na_rep="—"), width="stretch")
        if dados_[tk]["moeda"] != "BRL":
            st.caption(f"Valores na moeda do balanço ({dados_[tk]['moeda']}).")

    st.markdown("#### Valor estimado por fluxo de caixa descontado (DCF)")
    c1, c2, c3 = st.columns(3)
    taxa = est.slider("dcf_taxa", "Taxa de desconto", 8.0, 20.0, 12.0, 0.5, onde=c1, format="%.1f%%") / 100
    g = est.slider("dcf_g", "Crescimento do FCL (5 anos)", -5.0, 15.0, 4.0, 0.5, onde=c2, format="%.1f%%") / 100
    gp = est.slider("dcf_gp", "Crescimento na perpetuidade", 0.0, 5.0, 3.0, 0.5, onde=c3, format="%.1f%%") / 100

    linhas = []
    for t, d in dados_.items():
        valor, base = val.dcf(dados.buscar_caixa(t), d["acoes"], d["moeda"], taxa, g, gp)
        margem = (valor - d["preco"]) / valor * 100 if valor and d["preco"] else None
        linhas.append({"Ticker": t, "FCL médio 3a (R$ mi)": base / 1e6 if base is not None and not pd.isna(base) else None,
                       "Valor DCF": valor, "Preço": d["preco"], "Margem (%)": margem})
    st.dataframe(pd.DataFrame(linhas).style.format({
        "FCL médio 3a (R$ mi)": "{:,.0f}", "Valor DCF": "R$ {:.2f}", "Preço": "R$ {:.2f}",
        "Margem (%)": "{:.1f}%"}, na_rep="—"), width="stretch", hide_index=True)
    st.caption("Aproximação: usa a média do fluxo de caixa livre dos últimos 3 anos como fluxo ao acionista, "
               "sem ajustar dívida líquida. Não é adequado para bancos e holdings financeiras, e fica em branco "
               "quando o FCL é negativo ou o balanço não está em reais. Para escolher outros anos, use a página da empresa.")


def pagina_dividendos(dados_, per):
    hoje = datetime.now()
    parc = ano_parcial_no_periodo(per, hoje)
    series = {tk: filtrar_por_ano(dados.buscar_dividendos(tk), per, incluir_parcial=True, hoje=hoje) for tk in dados_}
    fig = go.Figure()
    for tk, s in series.items():
        if len(s):
            fig.add_bar(x=[f"{a} (parcial)" if a == parc else str(a) for a in s.index], y=s.values, name=tk)
    fig.update_layout(barmode="group", title="Dividendos por ação (R$/ano)", height=360, colorway=COLORWAY, **PLOT)
    fig.update_yaxes(**GRID)
    if fig.data:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dividendos registrados nos anos selecionados.")
    if parc:
        st.caption(f"{parc} está em andamento: os valores do ano atual são parciais e não devem ser comparados com anos completos.")

    linhas = []
    for t, d in dados_.items():
        p = d["preco"]
        linhas.append({"Ticker": t, "Proventos 12m": d["div_12m"], "Média 5 anos": d["div_medio"],
                       "DY 12m (%)": d["div_12m"] / p * 100 if p and d["div_12m"] is not None else None,
                       "DY s/ média 5a (%)": d["div_medio"] / p * 100 if p and d["div_medio"] else None})
    st.dataframe(pd.DataFrame(linhas).style.format({
        "Proventos 12m": "R$ {:.2f}", "Média 5 anos": "R$ {:.2f}",
        "DY 12m (%)": "{:.2f}%", "DY s/ média 5a (%)": "{:.2f}%"}, na_rep="—"),
        width="stretch", hide_index=True)
