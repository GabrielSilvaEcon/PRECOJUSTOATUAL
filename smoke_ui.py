"""Teste de fumaça da interface SEM Streamlit/Plotly/yfinance instalados: usa stubs e dados fictícios.
Executa app.py em cada página/seção para achar NameError, KeyError, TypeError etc.
(Não valida aparência nem APIs reais.)"""
import os, runpy, sys, types, traceback
import numpy as np, pandas as pd

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)


class S:
    def __init__(s, *a, **k): pass
    def __call__(s, *a, **k): return S()
    def __getattr__(s, n): return S()
    def __iter__(s): return iter([])
    def __enter__(s): return s
    def __exit__(s, *a): return False
    def __getitem__(s, k): return S()


class StopApp(Exception): pass


class SS(dict):
    def __getattr__(s, n):
        try: return s[n]
        except KeyError: raise AttributeError(n)
    def __setattr__(s, n, v): s[n] = v


st = types.ModuleType("streamlit")
st.session_state = SS()
AVISOS = []


class Col:
    def __getattr__(s, n): return getattr(st, n)
    def __enter__(s): return s
    def __exit__(s, *a): return False


def _val(key, default):
    if key is not None:
        st.session_state.setdefault(key, default)
        return st.session_state[key]
    return default

def selectbox(label, options, index=0, key=None, **k):
    options = list(options)
    return _val(key, options[index] if options else None)
def multiselect(label, options, default=None, key=None, **k):
    return _val(key, list(default or []))
def checkbox(label, value=False, key=None, **k): return _val(key, value)
def slider(label, mn, mx, value=None, step=None, key=None, **k): return _val(key, value)
def segmented_control(label, options, default=None, key=None, **k): return _val(key, default)
def columns(spec, **k): return [Col() for _ in range(spec if isinstance(spec, int) else len(spec))]
def tabs(l): return [Col() for _ in l]
def deco_cache(*a, **k):
    def wrap(f):
        f.clear = lambda: None
        return f
    return wrap(a[0]) if a and callable(a[0]) else wrap
deco_cache.clear = lambda: None
def stop(): raise StopApp()
def warning(m, *a, **k): AVISOS.append(("warning", str(m)))
def error(m, *a, **k): AVISOS.append(("error", str(m)))

for n, f in dict(selectbox=selectbox, multiselect=multiselect, checkbox=checkbox, slider=slider,
                 segmented_control=segmented_control, columns=columns, tabs=tabs, cache_data=deco_cache,
                 stop=stop, warning=warning, error=error).items():
    setattr(st, n, f)
for n in ["markdown", "caption", "metric", "plotly_chart", "info", "write", "divider", "set_page_config",
          "rerun", "link_button", "progress", "dataframe", "subheader", "text"]:
    setattr(st, n, lambda *a, **k: S())
st.text_input = lambda *a, **k: ""
st.number_input = lambda label, mn=None, mx=None, value=None, **k: value
st.button = lambda *a, **k: False
st.form_submit_button = lambda *a, **k: False
st.data_editor = lambda df, **k: df
for n in ["expander", "container", "form", "spinner"]:
    setattr(st, n, lambda *a, **k: Col())
st.sidebar = Col()
st.column_config = S()
comp = types.ModuleType("streamlit.components"); v1 = types.ModuleType("streamlit.components.v1")
v1.html = lambda *a, **k: None
st.components = comp; comp.v1 = v1
sys.modules.update({"streamlit": st, "streamlit.components": comp, "streamlit.components.v1": v1})

# plotly e yfinance falsos
for nome in ["plotly", "plotly.graph_objects", "plotly.subplots", "plotly.express"]:
    m = types.ModuleType(nome)
    m.__getattr__ = lambda n: S()
    sys.modules[nome] = m
sys.modules["plotly"].graph_objects = sys.modules["plotly.graph_objects"]
sys.modules["plotly"].subplots = sys.modules["plotly.subplots"]
pd.DataFrame.style = property(lambda self: S())

rng = np.random.default_rng(1)

class Ticker:
    def __init__(s, sym): s.sym = sym
    @property
    def info(s):
        return dict(shortName=f"Empresa {s.sym}", currentPrice=30.0, trailingEps=4.0, bookValue=25.0,
                    enterpriseToEbitda=5.0, returnOnEquity=.2, profitMargins=.1, debtToEquity=50,
                    sharesOutstanding=1e9, financialCurrency="BRL", sector="Financial Services", industry="Banks - Regional")
    def history(s, period=None, interval="1d", start=None, end=None, auto_adjust=False):
        idx = pd.bdate_range("2025-01-01", periods=400, tz="America/Sao_Paulo")
        c = 30 + np.cumsum(rng.normal(0, .5, len(idx)))
        return pd.DataFrame({"Open": c - .1, "High": c + .5, "Low": c - .5, "Close": c, "Volume": 1e6}, index=idx)
    @property
    def dividends(s):
        idx = pd.date_range("2019-03-31", "2026-06-30", freq="QE", tz="America/Sao_Paulo")
        return pd.Series(0.5, index=idx)
    @property
    def cashflow(s):
        cols = pd.to_datetime(["2025-12-31", "2024-12-31", "2023-12-31", "2022-12-31"])
        return pd.DataFrame({c: [5e9, -1e9, 4e9] for c in cols}, index=["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"])
    @property
    def quarterly_cashflow(s):
        cols = pd.to_datetime(["2026-06-30", "2026-03-31", "2025-12-31", "2025-09-30"])
        return pd.DataFrame({c: [1e9, -2e8, 8e8] for c in cols}, index=["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"])
    @property
    def income_stmt(s):
        cols = pd.to_datetime(["2025-12-31", "2024-12-31", "2023-12-31", "2022-12-31"])
        return pd.DataFrame({c: [9e9, 3e9, 2e9] for c in cols}, index=["Total Revenue", "Net Income", "EBITDA"])
    @property
    def quarterly_income_stmt(s):
        cols = pd.to_datetime(["2026-06-30", "2026-03-31", "2025-12-31", "2025-09-30"])
        return pd.DataFrame({c: [2e9, 5e8, 6e8] for c in cols}, index=["Total Revenue", "Net Income", "EBITDA"])

class Search:
    def __init__(s, q, max_results=10): s.quotes = [{"symbol": "WEGE3.SA", "shortname": "WEG"}]
yf = types.ModuleType("yfinance"); yf.Ticker = Ticker; yf.Search = Search
sys.modules["yfinance"] = yf

import macro, macro_core as core
MODO_REDE = {"ok": True}

def fake_json(url, params=None, tentativas=2):
    if not MODO_REDE["ok"]:
        raise RuntimeError("sem rede (simulado)")
    if "bcdata" in url:
        a = pd.to_datetime(params["dataInicial"], format="%d/%m/%Y"); b = pd.to_datetime(params["dataFinal"], format="%d/%m/%Y")
        datas = pd.date_range(a, b, freq="ME")
        return [{"data": d.strftime("%d/%m/%Y"), "valor": str(10 + i * .01)} for i, d in enumerate(datas)]
    cab = {"V": "Valor", "D1C": "Brasil (Código)", "D2C": "Variável (Código)", "D2N": "Variável", "D3C": "Trimestre (Código)"}
    nome = "Taxa trimestral (base: igual trimestre do ano anterior)"
    linhas = [{"V": "2.1", "D2N": nome, "D3C": f"{y}0{q}"} for y in range(2018, 2027) for q in (1, 2, 3, 4)]
    if "8888" in url or "8880" in url or "6390" in url:
        cab["D3C"] = "Mês (Código)"
        linhas = [{"V": "1.5", "D2N": "Variação mês/mesmo mês do ano anterior rendimento médio real habitual",
                   "D3C": f"{y}{m:02d}"} for y in range(2018, 2027) for m in range(1, 13)]
    return [cab] + linhas
macro._get_json = fake_json


def rodar(nav, **extras):
    st.session_state.clear(); AVISOS.clear()
    st.session_state["_p_nav"] = nav
    st.session_state.update(extras)
    try:
        runpy.run_path("app.py", run_name="__main__")
    except StopApp:
        pass


falhas = []
def caso(nome, nav, **extras):
    try:
        rodar(nav, **extras)
        print("ok  ", nome, f"({len(AVISOS)} avisos)")
    except Exception:
        falhas.append(nome); print("FALHA", nome); traceback.print_exc(limit=6)

for sec in ["Resumo", "Fundamentalista", "Valuation", "Técnica", "Contexto econômico"]:
    caso(f"Empresa/{sec}", "Empresa", _p_emp_sec=sec)
caso("Empresa/Fundamentalista trimestral", "Empresa", _p_emp_sec="Fundamentalista", _p_vis_PETR4="Trimestral",
     _p_emp_ticker="PETR4")
caso("Empresa/Valuation hist. do período", "Empresa", _p_emp_sec="Valuation", _p_val_hist="Anos do período selecionado")
caso("Empresa/Parcial atual", "Empresa", _p_emp_sec="Fundamentalista", _p_per_PETR4_opc="Ano atual e anterior",
     _p_parcial_PETR4=True)
caso("Empresa/Intervalo custom", "Empresa", _p_emp_sec="Fundamentalista", _p_per_PETR4_opc="Intervalo personalizado",
     _p_per_PETR4_ini=2020, _p_per_PETR4_fim=2024)
for sec in ["Valuation", "Fluxo de caixa", "Preço justo", "Dividendos"]:
    caso(f"Comparar/{sec}", "Comparar ações", _p_cmp_sec=sec)
caso("Dashboard/Ações", "Dashboard")
caso("Dashboard/Todos", "Dashboard", _p_dash_fontes=["Ações", "Macroeconomia", "Setores"], _p_dash_macro_graf=True)
caso("Macro/Geral", "Macroeconomia", _p_macro_grupos=["Juros e inflação", "Atividade e PIB", "Emprego e renda", "Fiscal"])
caso("Macro/Detalhes", "Macroeconomia", _p_macro_visao="Detalhes", _p_macro_tab=True, _p_macro_cmp=True)
caso("Setores/Geral", "Setores")
caso("Setores/Detalhes", "Setores", _p_set_visao="Detalhes", _p_set_tab=True, _p_set_cmp=True)
MODO_REDE["ok"] = False
macro._serie_cache.clear() if hasattr(macro._serie_cache, "clear") else None
caso("Macro SEM REDE", "Macroeconomia", _p_macro_visao="Detalhes")
caso("Setores SEM REDE", "Setores")
caso("Empresa contexto SEM REDE", "Empresa", _p_emp_sec="Contexto econômico")
caso("Empresa valuation SEM REDE", "Empresa", _p_emp_sec="Valuation")

# ---- cadastro: adicionar / remover / persistir / abrir empresa
import estado as est, json, tempfile
est.ARQUIVO = os.path.join(tempfile.mkdtemp(), "carteira.json")
st.session_state.clear(); est.iniciar()
assert st.session_state.cadastro == ["PETR4", "ITSA4", "BBAS3", "VALE3"]
assert est.adicionar(["WEGE3", "PETR4"]) == ["WEGE3"]
assert "WEGE3" in est.acompanhando() and len(st.session_state.cadastro) == 5
est.remover(["ITSA4"])
assert "ITSA4" not in st.session_state.cadastro and "ITSA4" not in est.acompanhando()
salvo = json.load(open(est.ARQUIVO)); assert "WEGE3" in salvo["cadastro"] and "ITSA4" not in salvo["cadastro"]
st.session_state.clear(); est.iniciar()                      # "nova sessão" lê o arquivo
assert st.session_state.cadastro == salvo["cadastro"]
st.session_state["_p_acomp"] = ["PETR4"]; est.ir_para_empresa("VALE3")
assert est.lembrado("nav") == "Empresa" and est.lembrado("emp_ticker") == "VALE3" and "VALE3" in est.acompanhando()
print("ok   cadastro (adicionar/remover/persistir/abrir empresa)")
print("\nFALHAS:", falhas or "nenhuma")
sys.exit(1 if falhas else 0)
