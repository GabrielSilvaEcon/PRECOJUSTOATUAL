"""Cálculos de valuation (lógica pura). Graham, Bazin e DCF vêm do app original."""
from math import sqrt

import pandas as pd

from periodos import Periodo, anos_completos


# ---------------------------------------------------------------- original (preservado)
def analisar(d: dict, metodo: str, yield_alvo: float, margem_alvo: float) -> dict:
    graham = None
    if d["lpa"] and d["vpa"] and d["lpa"] > 0 and d["vpa"] > 0:
        graham = sqrt(22.5 * d["lpa"] * d["vpa"])

    bazin = None
    if d["div_medio"] and d["div_medio"] > 0:
        bazin = d["div_medio"] / (yield_alvo / 100)

    if metodo == "Graham":
        justo = graham
    elif metodo == "Bazin":
        justo = bazin
    else:
        vals = [v for v in (graham, bazin) if v]
        justo = sum(vals) / len(vals) if vals else None

    margem = None
    if justo and d["preco"]:
        margem = (justo - d["preco"]) / justo * 100

    if margem is None:
        status, cls = "Sem dados", "na"
    elif margem >= margem_alvo:
        status, cls = "Com margem", "good"
    elif margem >= 0:
        status, cls = "Preço justo", "fair"
    else:
        status, cls = "Acima do justo", "bad"

    return {**d, "graham": graham, "bazin": bazin, "justo": justo,
            "margem": margem, "status": status, "cls": cls}


def multiplos(d: dict) -> dict:
    p = d["preco"]
    return {
        "pl": p / d["lpa"] if p and d["lpa"] and d["lpa"] > 0 else None,
        "pvp": p / d["vpa"] if p and d["vpa"] and d["vpa"] > 0 else None,
        "dy": d["div_12m"] / p * 100 if p and d["div_12m"] is not None else None,
        "roe": d["roe"] * 100 if d["roe"] is not None else None,
        "margem": d["margem_liq"] * 100 if d["margem_liq"] is not None else None,
    }


def dcf(caixa: pd.DataFrame, acoes, moeda: str, taxa: float, g: float, gp: float, n_anos: int = 3):
    """Valor por ação a partir da média do FCL dos últimos `n_anos` (padrão 3, como no original)."""
    if moeda != "BRL" or not acoes or caixa.empty or "Fluxo de caixa livre" not in caixa:
        return None, None
    base = caixa["Fluxo de caixa livre"].dropna().tail(n_anos).mean()
    if pd.isna(base) or base <= 0:
        return None, base
    if taxa <= gp:  # evita divisão por zero/negativa na perpetuidade
        return None, base
    pv = sum(base * (1 + g) ** t / (1 + taxa) ** t for t in range(1, 6))
    vt = base * (1 + g) ** 5 * (1 + gp) / (taxa - gp)
    return (pv + vt / (1 + taxa) ** 5) / acoes, base


# ---------------------------------------------------------------- histórico selecionável
def div_medio_periodo(div_anuais: pd.Series, p: Periodo, hoje=None):
    """Média de dividendos/ação só dos anos COMPLETOS do período. Retorna (média, anos_usados)."""
    if div_anuais is None or len(div_anuais) == 0:
        return None, []
    usados = [a for a in anos_completos(p, hoje) if a in div_anuais.index]
    if not usados:
        return None, []
    return float(div_anuais.loc[usados].mean()), usados


def caixa_periodo(caixa: pd.DataFrame, p: Periodo, hoje=None):
    """FCL anual restrito aos anos completos do período. Retorna (DataFrame, anos_usados)."""
    if caixa is None or caixa.empty:
        return pd.DataFrame(), []
    usados = [a for a in anos_completos(p, hoje) if a in caixa.index]
    return caixa.loc[usados], usados


# ---------------------------------------------------------------- cenários
ALAVANCAS = [
    ("taxa", "Taxa de desconto (p.p.)", "DCF"),
    ("g", "Crescimento do FCL (p.p.)", "DCF"),
    ("lpa", "LPA (%)", "Graham"),
    ("div", "Dividendos médios (%)", "Bazin"),
    ("yield", "Yield exigido (p.p.)", "Bazin"),
]
CENARIOS = ["Pessimista", "Base", "Otimista"]

# Valores ILUSTRATIVOS (estimativas do usuário/app, não dados oficiais). Editáveis na tela.
DELTAS_PADRAO = {
    "Pessimista": {"taxa": 2.0, "g": -2.0, "lpa": -15.0, "div": -15.0, "yield": 1.0},
    "Base": {"taxa": 0.0, "g": 0.0, "lpa": 0.0, "div": 0.0, "yield": 0.0},
    "Otimista": {"taxa": -1.5, "g": 2.0, "lpa": 10.0, "div": 10.0, "yield": -1.0},
}


def calcular_cenario(d: dict, caixa: pd.DataFrame, base: dict, delta: dict, metodo: str = "Média"):
    """`base`: yield_alvo, taxa, g, gp (em %), n_fcl. `delta`: variações por alavanca.
    Devolve valores e as linhas de cálculo (para mostrar a conta ao usuário)."""
    linhas = []
    lpa = d["lpa"] * (1 + delta["lpa"] / 100) if d.get("lpa") else None
    vpa = d.get("vpa")
    graham = None
    if lpa and vpa and lpa > 0 and vpa > 0:
        graham = sqrt(22.5 * lpa * vpa)
        linhas.append(f"Graham = √(22,5 × {lpa:.2f} × {vpa:.2f}) = {graham:.2f}")
    else:
        linhas.append("Graham: indisponível (LPA ou VPA ausente/não positivo)")

    div = d["div_medio"] * (1 + delta["div"] / 100) if d.get("div_medio") else None
    y = max(1.0, base["yield_alvo"] + delta["yield"])
    bazin = None
    if div and div > 0:
        bazin = div / (y / 100)
        linhas.append(f"Bazin = {div:.2f} ÷ {y:.1f}% = {bazin:.2f}")
    else:
        linhas.append("Bazin: indisponível (sem dividendos no histórico escolhido)")

    taxa = (base["taxa"] + delta["taxa"]) / 100
    g = (base["g"] + delta["g"]) / 100
    gp = base["gp"] / 100
    valor_dcf, fcl = dcf(caixa, d.get("acoes"), d.get("moeda", "BRL"), taxa, g, gp, n_anos=base["n_fcl"])
    if valor_dcf:
        linhas.append(f"DCF: FCL base {fcl/1e6:,.0f} mi · taxa {taxa*100:.1f}% · crescimento {g*100:.1f}% "
                      f"· perpetuidade {gp*100:.1f}% → {valor_dcf:.2f}")
    else:
        linhas.append("DCF: indisponível (FCL ≤ 0, balanço fora de R$, sem dados, ou taxa ≤ perpetuidade)")

    if metodo == "Graham":
        justo = graham
    elif metodo == "Bazin":
        justo = bazin
    else:
        vals = [v for v in (graham, bazin) if v]
        justo = sum(vals) / len(vals) if vals else None
    margem = (justo - d["preco"]) / justo * 100 if justo and d.get("preco") else None
    return {"graham": graham, "bazin": bazin, "dcf": valor_dcf, "justo": justo,
            "margem": margem, "linhas": linhas}
