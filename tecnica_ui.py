"""Página de análise técnica (do app original) para UMA empresa.
Mudanças: o ativo vem de fora e há a opção de seguir o filtro de anos da empresa."""
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import dados
import estado as est
import tecnica as tec
from estilo import BG
from periodos import Periodo


def tradingview(ticker: str, intervalo: str, altura: int):
    """Gráfico limpo oficial do TradingView (widget embutido, sem sinais)."""
    cfg = {
        "autosize": True, "symbol": f"BMFBOVESPA:{ticker}", "interval": intervalo,
        "timezone": "America/Sao_Paulo", "theme": "dark", "style": "1", "locale": "br",
        "enable_publishing": False, "hide_side_toolbar": True, "allow_symbol_change": False,
        "backgroundColor": BG, "toolbar_bg": BG, "gridColor": "#262a33", "container_id": "tv_chart",
    }
    html = f"""
    <style>body{{margin:0;background:{BG};}}</style>
    <div style="height:{altura}px;width:100%;"><div id="tv_chart" style="height:100%;width:100%;"></div></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>new TradingView.widget({json.dumps(cfg)});</script>"""
    components.html(html, height=altura)


def pagina(ticker: str, periodo: Periodo):
    c1, c2, c3, c4 = st.columns([1, 1, 1.2, 1.4])
    tf = est.selectbox("tec_tf", "Timeframe", ["Diário", "Semanal"], onde=c1)
    seguir = est.checkbox("tec_seguir", f"Usar anos {periodo.rotulo}", padrao=False, onde=c2,
                          help="Se marcado, o gráfico usa as datas do filtro de anos (o ano atual vai até hoje).")
    periodo_lbl = est.selectbox("tec_per", "Período", ["6 meses", "1 ano", "2 anos", "5 anos"], padrao="1 ano",
                                onde=c3, disabled=seguir)
    layout = est.selectbox("tec_layout", "Exibição", ["Empilhado", "Lado a lado"], onde=c4)

    with st.expander("Sinais e parâmetros"):
        e1, e2 = st.columns(2)
        grupos = est.multiselect("tec_grupos", "Grupos de sinais",
                                 ["Candlestick", "Padrões gráficos", "Indicadores (MM, IFR, volume)"],
                                 padrao=["Candlestick", "Padrões gráficos", "Indicadores (MM, IFR, volume)"], onde=e1)
        candles_sel = e2.multiselect("Padrões de candle", tec.CANDLE_NOMES,
                                     default=[n for n in tec.CANDLE_NOMES if n != "Doji"])
        p1, p2, p3 = st.columns(3)
        mm_c = p1.number_input("Média móvel curta", 5, 100, 21)
        mm_l = p2.number_input("Média móvel longa", 10, 300, 50)
        mostrar_mm = p3.checkbox("Mostrar médias no gráfico", value=True)

    intervalo, tv_int = {"Diário": ("1d", "D"), "Semanal": ("1wk", "W")}[tf]
    if seguir:
        ini = f"{periodo.ini}-01-01"
        fim = min(datetime.now(), datetime(periodo.fim, 12, 31)).strftime("%Y-%m-%d")
        df = dados.historico_intervalo(ticker, ini, fim, intervalo)
        if periodo.fim >= datetime.now().year:
            st.caption(f"O ano {datetime.now().year} está em andamento: o gráfico vai até hoje.")
    else:
        periodo_yf = {"6 meses": "6mo", "1 ano": "1y", "2 anos": "2y", "5 anos": "5y"}[periodo_lbl]
        df = dados.historico(ticker, periodo_yf, intervalo)
    if df.empty or len(df) < 30:
        st.warning("Histórico insuficiente para esse ativo/período. Tente um período maior.")
        return

    sinais, padroes, niveis = [], [], []
    ind = tec.indicadores(df, int(mm_c), int(mm_l))
    if "Candlestick" in grupos:
        sinais += [s for s in tec.candlesticks(df) if s["sinal"] in candles_sel]
    if "Padrões gráficos" in grupos:
        padroes, niveis = tec.padroes_graficos(df)
    if "Indicadores (MM, IFR, volume)" in grupos:
        sinais += ind["sinais"]

    corte = df.index[-10]
    rec = [s for s in sinais + padroes if s["data"] >= corte]
    m1, m2, m3 = st.columns(3)
    m1.metric("Sinais de alta (10 candles)", sum(s["tipo"] == "alta" for s in rec))
    m2.metric("Sinais de baixa (10 candles)", sum(s["tipo"] == "baixa" for s in rec))
    m3.metric("Indecisão (10 candles)", sum(s["tipo"] == "neutro" for s in rec))

    link = f"https://br.tradingview.com/chart/?symbol=BMFBOVESPA%3A{ticker}"
    lado = layout == "Lado a lado"
    alt_tv, alt_sinais = (620, 620) if lado else (520, 720)

    def bloco_limpo():
        st.markdown("#### Gráfico limpo · TradingView")
        tradingview(ticker, tv_int, alt_tv)
        st.link_button("Abrir no TradingView ↗", link)

    def bloco_sinais():
        st.markdown("#### Gráfico com sinais")
        fig = tec.figura(df, sinais, padroes, niveis, ind, diario=(tf == "Diário"),
                         altura=alt_sinais, mostrar_mm=mostrar_mm)
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

    if lado:
        a, b = st.columns(2)
        with a:
            bloco_limpo()
        with b:
            bloco_sinais()
    else:
        bloco_limpo()
        bloco_sinais()

    st.markdown("#### Sinais recentes")
    linhas = [{"Data": s["data"], "Categoria": s["categoria"], "Sinal": s["sinal"],
               "Viés": s["tipo"].capitalize(), "Preço": s["preco"]} for s in sinais]
    linhas += [{"Data": p["data"], "Categoria": p["categoria"], "Sinal": p["nome"],
                "Viés": p["tipo"].capitalize(), "Preço": p["preco"]} for p in padroes]
    if linhas:
        tabela = pd.DataFrame(linhas).sort_values("Data", ascending=False).head(30)
        st.dataframe(tabela, width="stretch", hide_index=True, column_config={
            "Data": st.column_config.DatetimeColumn(format="DD/MM/YYYY"),
            "Preço": st.column_config.NumberColumn(format="R$ %.2f"),
        })
    else:
        st.caption("Nenhum sinal detectado com os filtros atuais.")
    if niveis:
        st.caption("Níveis detectados: " + " · ".join(
            f"{n['tipo']} R$ {n['preco']:.2f} ({n['toques']} toques)" for n in niveis))
    st.caption("O gráfico limpo é o widget oficial do TradingView. Os sinais são detectados pelo app com regras "
               "simples sobre os dados do Yahoo Finance (o TradingView não permite buscar os desenhos ou sinais "
               "de volta), então podem divergir do que você marcaria à mão.")
