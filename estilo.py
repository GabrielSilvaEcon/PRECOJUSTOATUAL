"""Paleta, CSS e formatadores (idênticos ao app original, com poucos acréscimos)."""
import pandas as pd
import streamlit as st

BG, SURFACE, BORDER = "#15171c", "#1b1e25", "#2a2e37"
TEXT, MUTED = "#cfd3da", "#8b919c"
ACCENT = "#8aa0b8"
GOOD, FAIR, BAD = "#7fae93", "#c2ad7e", "#c08580"
COLORWAY = ["#6b7a8f", "#7fae93", "#c2ad7e", "#c08580", "#9a8fb0", "#8fb0ad"]

PLOT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": TEXT}, margin=dict(l=10, r=10, t=40, b=10))
GRID = dict(gridcolor="#262a33", zeroline=False)


def aplicar():
    st.markdown(f"""
<style>
.stApp {{background:{BG};}}
header[data-testid="stHeader"] {{background:transparent;}}
section[data-testid="stSidebar"] {{background:{SURFACE}; border-right:1px solid {BORDER};}}
.block-container {{padding-top:2.2rem; max-width:1400px;}}
.topo {{display:flex; align-items:baseline; gap:14px; padding-bottom:10px;
        border-bottom:1px solid {BORDER}; margin-bottom:14px;}}
.hero {{font-size:1.45rem; font-weight:700; color:#d9dce2; letter-spacing:.2px;}}
.sub {{font-size:.78rem; color:{MUTED};}}
.card {{background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px;
        padding:16px 18px; margin-bottom:10px;}}
.tk {{font-size:1.3rem; font-weight:700; letter-spacing:.4px;}}
.nm {{font-size:.78rem; color:{MUTED}; margin-bottom:8px;}}
.aviso {{font-size:.72rem; color:{FAIR}; margin-top:6px;}}
.badge {{display:inline-block; padding:3px 11px; border-radius:999px;
         font-size:.72rem; font-weight:600; float:right;}}
.good {{background:rgba(127,174,147,.14); color:{GOOD};}}
.fair {{background:rgba(194,173,126,.14); color:{FAIR};}}
.bad  {{background:rgba(192,133,128,.14); color:{BAD};}}
.na   {{background:rgba(139,145,156,.14); color:{MUTED};}}
.lbl {{font-size:.68rem; color:{MUTED}; text-transform:uppercase; letter-spacing:.8px;}}
.val {{font-size:1.15rem; font-weight:600;}}
.fonte {{font-size:.72rem; color:{MUTED};}}
.etq {{display:inline-block; padding:1px 8px; border-radius:6px; font-size:.68rem; font-weight:600; margin-right:6px;}}
.etq-of {{background:rgba(127,174,147,.16); color:{GOOD};}}
.etq-in {{background:rgba(138,160,184,.16); color:{ACCENT};}}
.etq-es {{background:rgba(194,173,126,.16); color:{FAIR};}}
h4 {{font-weight:600; color:#d9dce2;}}
</style>""", unsafe_allow_html=True)


def brl(v):
    return "—" if v is None or pd.isna(v) else f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(v, casas=2, sufixo=""):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".") + sufixo


ETIQUETAS = ('<span class="etq etq-of">Dado oficial</span>'
             '<span class="etq etq-in">Interpretação</span>'
             '<span class="etq etq-es">Estimativa</span>')
