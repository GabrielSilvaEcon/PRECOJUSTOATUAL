"""Peças visuais reutilizadas: cartão da empresa e medidor de margem de segurança (do app original)."""
import plotly.graph_objects as go
import streamlit as st

from estilo import BAD, FAIR, GOOD, MUTED, PLOT, TEXT, brl


def gauge(margem):
    v = 0 if margem is None else max(-60, min(60, margem))
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=v,
        number={"suffix": "%", "font": {"size": 26, "color": TEXT}},
        gauge={
            "axis": {"range": [-60, 60], "tickcolor": "#5d6470"},
            "bar": {"color": "#aeb4bf", "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [
                {"range": [-60, 0], "color": "rgba(192,133,128,.30)"},
                {"range": [0, 20], "color": "rgba(194,173,126,.30)"},
                {"range": [20, 60], "color": "rgba(127,174,147,.30)"},
            ],
        },
    ))
    fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=0), **{
        k: v_ for k, v_ in PLOT.items() if k != "margin"})
    return fig


def cartao(r: dict):
    aviso = (f'<div class="aviso">Balanço em {r["moeda"]}: LPA/VPA podem não estar em R$</div>'
             if r["moeda"] != "BRL" else "")
    st.markdown(
        f"""<div class="card">
        <span class="badge {r['cls']}">{r['status']}</span>
        <div class="tk">{r['ticker']}</div>
        <div class="nm">{r['nome']}</div>
        <div style="display:flex; gap:22px;">
          <div><div class="lbl">Preço atual</div><div class="val">{brl(r['preco'])}</div></div>
          <div><div class="lbl">Preço justo</div><div class="val">{brl(r['justo'])}</div></div>
        </div>
        <div style="margin-top:10px;">
          <div class="lbl">Média de dividendos (5 anos)</div>
          <div class="val">{brl(r['div_medio'])} <span style="font-size:.72rem;color:{MUTED}">/ ano</span></div>
        </div>{aviso}</div>""",
        unsafe_allow_html=True,
    )


def margem_cor(m, alvo):
    return BAD if m < 0 else GOOD if m >= alvo else FAIR
