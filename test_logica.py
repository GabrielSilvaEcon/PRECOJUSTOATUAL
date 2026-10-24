import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import date, datetime
import pandas as pd, numpy as np
import periodos as P, valuation as V, macro_core as C, catalogo as K

H = datetime(2026, 10, 24)

def test_periodos():
    assert (P.resolver("Ano atual", hoje=H).ini, P.resolver("Ano atual", hoje=H).fim) == (2026, 2026)
    assert P.resolver("Ano anterior", hoje=H).anos == [2025]
    assert P.resolver("Ano atual e anterior", hoje=H).anos == [2025, 2026]
    assert P.resolver("Dois anos anteriores", hoje=H).anos == [2024, 2025]
    p5 = P.resolver("Últimos 5 anos", hoje=H)
    assert p5.anos == [2021, 2022, 2023, 2024, 2025]
    pc = P.resolver("Intervalo personalizado", 2025, 2022, hoje=H)  # invertido -> corrige
    assert (pc.ini, pc.fim) == (2022, 2025)
    p = P.resolver("Ano atual e anterior", hoje=H)
    assert P.anos_completos(p, H) == [2025] and P.ano_parcial_no_periodo(p, H) == 2026
    assert P.anos_completos(P.resolver("Ano atual", hoje=H), H) == []
    assert P.anos_faltantes([2023, 2024], [2022, 2023, 2024]) == [2022]
    s = pd.Series([1, 2, 3, 4], index=[2023, 2024, 2025, 2026])
    assert list(P.filtrar_por_ano(s, p, hoje=H).index) == [2025]
    assert list(P.filtrar_por_ano(s, p, incluir_parcial=True, hoje=H).index) == [2025, 2026]
    assert P.rotulo_trimestre("2026-09-30") == "3T26"

def test_valuation():
    d = dict(lpa=4.0, vpa=25.0, div_medio=2.0, preco=30.0, acoes=1e9, moeda="BRL", div_12m=2.0,
             roe=.2, margem_liq=.1)
    r = V.analisar(d, "Média", 6.0, 20)
    assert abs(r["graham"] - (22.5 * 4 * 25) ** .5) < 1e-9 and abs(r["bazin"] - 2 / .06) < 1e-9
    assert r["status"] in {"Com margem", "Preço justo", "Acima do justo"}
    cx = pd.DataFrame({"Fluxo de caixa livre": [1e9, 2e9, 3e9, 4e9]}, index=[2021, 2022, 2023, 2024])
    v3, b3 = V.dcf(cx, 1e9, "BRL", .12, .04, .03)
    assert abs(b3 - 3e9) < 1 and v3 > 0
    v2, b2 = V.dcf(cx, 1e9, "BRL", .12, .04, .03, n_anos=2)
    assert abs(b2 - 3.5e9) < 1
    assert V.dcf(cx, 1e9, "BRL", .03, .04, .03)[0] is None          # taxa <= perpetuidade
    assert V.dcf(cx, 1e9, "USD", .12, .04, .03)[0] is None
    p = P.resolver("Intervalo personalizado", 2022, 2026, hoje=H)
    sub, anos = V.caixa_periodo(cx, p, H)
    assert anos == [2022, 2023, 2024]
    m, usados = V.div_medio_periodo(pd.Series([1., 3., 5.], index=[2024, 2025, 2026]), P.resolver("Ano atual e anterior", hoje=H), H)
    assert m == 3.0 and usados == [2025]                              # 2026 parcial ignorado
    assert V.div_medio_periodo(pd.Series([1.], index=[2026]), P.resolver("Ano atual", hoje=H), H) == (None, [])

def test_cenarios():
    d = dict(lpa=4.0, vpa=25.0, div_medio=2.0, preco=30.0, acoes=1e9, moeda="BRL")
    cx = pd.DataFrame({"Fluxo de caixa livre": [3e9] * 3}, index=[2022, 2023, 2024])
    base = dict(yield_alvo=6.0, taxa=12.0, g=4.0, gp=3.0, n_fcl=3)
    res = {n: V.calcular_cenario(d, cx, base, V.DELTAS_PADRAO[n]) for n in V.CENARIOS}
    assert res["Pessimista"]["justo"] < res["Base"]["justo"] < res["Otimista"]["justo"]
    assert res["Pessimista"]["dcf"] < res["Base"]["dcf"] < res["Otimista"]["dcf"]
    # Base == cálculo original sem alavancas
    orig = V.analisar({**d, "div_12m": 0, "roe": None, "margem_liq": None}, "Média", 6.0, 20)
    assert abs(res["Base"]["justo"] - orig["justo"]) < 1e-9
    assert any("Graham" in l for l in res["Base"]["linhas"])
    sem = V.calcular_cenario({**d, "lpa": None, "div_medio": None}, pd.DataFrame(), base, V.DELTAS_PADRAO["Base"])
    assert sem["justo"] is None and sem["margem"] is None

def test_sgs_e_nao_zerar():
    df = C.parse_sgs([{"data": "01/01/2024", "valor": "0.5"}, {"data": "01/02/2024", "valor": ""},
                      {"data": "01/03/2024", "valor": "1,25"}, {"data": "01/03/2024", "valor": "9"}])
    assert len(df) == 2 and list(df["valor"]) == [0.5, 1.25]          # vazio descartado, não vira 0
    assert C.parse_sgs([]).empty and C.parse_sgs([{"x": 1}]).empty

def test_janelas():
    j = C.janelas(date(2011, 1, 1), date(2026, 10, 24))
    assert j[0][0] == date(2011, 1, 1) and j[-1][1] == date(2026, 10, 24)
    assert all((b - a).days <= 9 * 366 for a, b in j)
    assert all(j[i][1] < j[i + 1][0] for i in range(len(j) - 1))

def test_sidra():
    cab = {"NC": "Nível Territorial (Código)", "V": "Valor", "D1C": "Brasil (Código)", "D2C": "Variável (Código)",
           "D2N": "Variável", "D3C": "Trimestre (Código)", "D3N": "Trimestre"}
    linhas = [cab,
              {"V": "2.5", "D2N": "Taxa trimestral (base: igual trimestre do ano anterior)", "D3C": "202401"},
              {"V": "...", "D2N": "Taxa trimestral (base: igual trimestre do ano anterior)", "D3C": "202402"},
              {"V": "3.0", "D2N": "Taxa trimestral (base: igual trimestre do ano anterior)", "D3C": "202403"},
              {"V": "9.9", "D2N": "Taxa acumulada em quatro trimestres", "D3C": "202403"}]
    df = C.parse_sidra(linhas, ("igual trimestre",))
    assert list(df["valor"]) == [2.5, 3.0] and df["data"].iloc[0] == pd.Timestamp("2024-03-31")
    assert df["data"].iloc[1] == pd.Timestamp("2024-09-30")
    try:
        C.parse_sidra(linhas, ("inexistente",)); assert False
    except ValueError as e:
        assert "Disponíveis" in str(e)
    cab2 = {**cab, "D3C": "Trimestre Móvel (Código)"}
    df2 = C.parse_sidra([cab2, {"V": "6.1", "D2N": "Taxa", "D3C": "202405"}], ())
    assert df2["data"].iloc[0] == pd.Timestamp("2024-05-31")          # móvel = mês, não trimestre

def test_variacoes_status():
    datas = pd.date_range("2025-01-31", periods=22, freq="ME")
    df = pd.DataFrame({"data": datas, "valor": np.arange(22) + 100.0})
    v = C.variacoes(df, "pct")
    assert v["ultimo"] == 121.0 and abs(v["var_anterior"] - (121 / 120 - 1) * 100) < 1e-9
    assert v["var_12m"] is not None
    assert C.variacoes(df, "pp")["var_anterior"] == 1.0
    assert C.variacoes(C.vazio(), "pp") == {}
    assert C.desatualizada(pd.Timestamp("2026-01-31"), "mensal", H) and not C.desatualizada(pd.Timestamp("2026-10-20"), "diaria", H)
    r = C.resumo_anual(df, "mensal", H)
    assert r.loc[2025, "Status"] == "completo" and "parcial" in r.loc[2026, "Status"]
    inc = C.resumo_anual(df[df["data"] < "2025-07-01"], "mensal", H)
    assert "incompleto" in inc.loc[2025, "Status"]
    m = C.sobrepor_anos(df, [2025, 2026])
    assert set(m.columns) == {2025, 2026}

def test_catalogo_setor():
    assert K.mapear_setor("WEGE3")[0] == "Indústria"
    assert K.mapear_setor("XXXX3", "Utilities", "Utilities - Regulated Electric")[0] == "Energia elétrica"
    assert K.mapear_setor("XXXX3", None, None)[0] is None
    for s, v in K.SETORES.items():
        for i in v["indicadores"]:
            assert i in K.CATALOGO and i in v["porque"]
        assert set(v["afeta"]) == {"Receitas", "Custos", "Margens", "Riscos"}

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
