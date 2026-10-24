"""Parsers e cálculos das séries econômicas (lógica pura, sem rede e sem Streamlit)."""
from datetime import date, datetime, timedelta

import pandas as pd

LIMITE_DESATUALIZADA = {"diaria": 10, "mensal": 75, "trimestral": 150}   # dias
ESPERADO_POR_ANO = {"diaria": 200, "mensal": 12, "trimestral": 4}


def janelas(ini: date, fim: date, anos: int = 9):
    """Divide [ini, fim] em janelas de até `anos` anos (o SGS limita consultas de séries diárias)."""
    out, atual = [], ini
    while atual <= fim:
        try:
            limite = atual.replace(year=atual.year + anos) - timedelta(days=1)
        except ValueError:  # 29/02
            limite = atual.replace(year=atual.year + anos, day=28)
        out.append((atual, min(limite, fim)))
        atual = limite + timedelta(days=1)
    return out


def vazio() -> pd.DataFrame:
    return pd.DataFrame({"data": pd.to_datetime([]), "valor": pd.Series([], dtype=float)})


def parse_sgs(linhas: list) -> pd.DataFrame:
    """[{'data':'01/02/2024','valor':'0.50'}] -> DataFrame(data, valor). Valores inválidos são descartados
    (nunca viram zero)."""
    if not linhas:
        return vazio()
    df = pd.DataFrame(linhas)
    if not {"data", "valor"} <= set(df.columns):
        return vazio()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df = df.dropna(subset=["data", "valor"]).drop_duplicates("data")
    return df.sort_values("data").reset_index(drop=True)[["data", "valor"]]


def _fim_do_mes(ano: int, mes: int) -> pd.Timestamp:
    return pd.Timestamp(year=ano, month=mes, day=1) + pd.offsets.MonthEnd(0)


def parse_sidra(linhas: list, palavras: tuple = ()) -> pd.DataFrame:
    """Converte a resposta da API SIDRA (1ª linha = cabeçalho) em DataFrame(data, valor).
    Escolhe a variável cujo nome contém alguma das `palavras`; se nenhuma casar, levanta ValueError
    listando as variáveis disponíveis (para o usuário ajustar o catálogo)."""
    if not linhas or len(linhas) < 2:
        return vazio()
    cab, dados = linhas[0], linhas[1:]
    chave_per = next((k for k, v in cab.items() if k.startswith("D") and k.endswith("C")
                      and str(v).lower().startswith(("trimestre", "mês", "mes", "ano"))), None)
    chave_var = next((k for k, v in cab.items() if k.startswith("D") and k.endswith("N")
                      and str(v).lower().startswith("variável")), None)
    if not chave_per:
        raise ValueError("Resposta do IBGE sem coluna de período reconhecível.")
    tipo_per = str(cab[chave_per]).lower()
    trimestral = tipo_per.startswith("trimestre") and "móvel" not in tipo_per and "movel" not in tipo_per

    if chave_var:
        nomes = list(dict.fromkeys(r.get(chave_var, "") for r in dados))
        escolhido = None
        for p in palavras:
            escolhido = next((n for n in nomes if p.lower() in n.lower()), None)
            if escolhido:
                break
        if palavras and not escolhido:
            raise ValueError("Variável não encontrada no IBGE. Disponíveis: " + "; ".join(nomes[:8]))
        if not palavras:
            escolhido = nomes[0] if nomes else None
        dados = [r for r in dados if r.get(chave_var) == escolhido]

    registros = []
    for r in dados:
        cod = str(r.get(chave_per, ""))
        try:
            ano = int(cod[:4])
            if len(cod) == 4:
                data = pd.Timestamp(year=ano, month=12, day=31)
            else:
                n = int(cod[4:6])
                data = _fim_do_mes(ano, n * 3 if trimestral else n)
        except (ValueError, TypeError):
            continue
        registros.append({"data": data, "valor": pd.to_numeric(r.get("V"), errors="coerce")})
    if not registros:
        return vazio()
    df = pd.DataFrame(registros).dropna().drop_duplicates("data").sort_values("data")
    return df.reset_index(drop=True)


def filtrar_anos(df: pd.DataFrame, ini: int, fim: int) -> pd.DataFrame:
    if df.empty:
        return df
    a = df["data"].dt.year
    return df[(a >= ini) & (a <= fim)].reset_index(drop=True)


def _delta(atual, base, var):
    if base is None or pd.isna(base):
        return None
    if var == "pp":
        return atual - base
    return (atual / base - 1) * 100 if base else None


def variacoes(df: pd.DataFrame, var: str) -> dict:
    """Último valor e variações contra o ponto anterior e contra ~12 meses antes (se existir)."""
    if df.empty:
        return {}
    ult = df.iloc[-1]
    ant = df.iloc[-2]["valor"] if len(df) > 1 else None
    alvo = ult["data"] - pd.Timedelta(days=365)
    antes = df[df["data"] <= alvo]
    v12 = None
    if not antes.empty and (alvo - antes.iloc[-1]["data"]).days <= 45:
        v12 = antes.iloc[-1]["valor"]
    return {"ultimo": float(ult["valor"]), "data": ult["data"],
            "var_anterior": _delta(ult["valor"], ant, var), "var_12m": _delta(ult["valor"], v12, var),
            "unidade_var": "p.p." if var == "pp" else "%"}


def desatualizada(ultima: pd.Timestamp, periodicidade: str, hoje: datetime = None) -> bool:
    hoje = hoje or datetime.now()
    return (hoje - ultima.to_pydatetime()).days > LIMITE_DESATUALIZADA.get(periodicidade, 90)


def resumo_anual(df: pd.DataFrame, periodicidade: str, hoje: datetime = None) -> pd.DataFrame:
    """Estatísticas por ano com status: completo / parcial (ano corrente) / incompleto (faltam observações)."""
    if df.empty:
        return pd.DataFrame()
    hoje = hoje or datetime.now()
    esperado = ESPERADO_POR_ANO.get(periodicidade, 12)
    g = df.groupby(df["data"].dt.year)["valor"]
    out = pd.DataFrame({"Média": g.mean(), "Último": g.last(), "Mínimo": g.min(),
                        "Máximo": g.max(), "Observações": g.count()})
    status = []
    for ano, n in out["Observações"].items():
        if ano >= hoje.year:
            status.append("parcial (ano em andamento)")
        elif n < esperado * 0.9:
            status.append(f"incompleto ({n} de ~{esperado})")
        else:
            status.append("completo")
    out["Status"] = status
    out.index.name = "Ano"
    return out


def sobrepor_anos(df: pd.DataFrame, anos: list) -> pd.DataFrame:
    """Matriz mês x ano (média mensal) para comparar anos de uma mesma série."""
    if df.empty:
        return pd.DataFrame()
    d = df[df["data"].dt.year.isin(anos)].copy()
    d["ano"], d["mes"] = d["data"].dt.year, d["data"].dt.month
    return d.pivot_table(index="mes", columns="ano", values="valor", aggfunc="mean")
