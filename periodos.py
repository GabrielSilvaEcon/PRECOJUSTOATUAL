"""Períodos e anos: lógica pura (sem Streamlit), fácil de testar.

Regras:
- Ano completo = ano anterior ao ano corrente. O ano corrente é sempre PARCIAL.
- "Últimos 5 anos" = os cinco anos COMPLETOS mais recentes (ano corrente fora).
- "Dois anos anteriores" = os dois anos completos imediatamente anteriores.
"""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

OPCOES = [
    "Ano atual",
    "Ano anterior",
    "Ano atual e anterior",
    "Dois anos anteriores",
    "Últimos 5 anos",
    "Intervalo personalizado",
]


@dataclass(frozen=True)
class Periodo:
    ini: int
    fim: int
    opcao: str = "Intervalo personalizado"

    @property
    def anos(self) -> list:
        return list(range(self.ini, self.fim + 1))

    @property
    def rotulo(self) -> str:
        return str(self.ini) if self.ini == self.fim else f"{self.ini}–{self.fim}"


def _ano(hoje=None) -> int:
    return (hoje or datetime.now()).year


def resolver(opcao: str, ano_ini=None, ano_fim=None, hoje=None) -> Periodo:
    y = _ano(hoje)
    if opcao == "Ano atual":
        return Periodo(y, y, opcao)
    if opcao == "Ano anterior":
        return Periodo(y - 1, y - 1, opcao)
    if opcao == "Ano atual e anterior":
        return Periodo(y - 1, y, opcao)
    if opcao == "Dois anos anteriores":
        return Periodo(y - 2, y - 1, opcao)
    if opcao == "Últimos 5 anos":
        return Periodo(y - 5, y - 1, opcao)
    i = int(ano_ini) if ano_ini is not None else y - 4
    f = int(ano_fim) if ano_fim is not None else y - 1
    if i > f:
        i, f = f, i
    return Periodo(i, f, "Intervalo personalizado")


def anos_completos(p: Periodo, hoje=None) -> list:
    y = _ano(hoje)
    return [a for a in p.anos if a < y]


def ano_parcial_no_periodo(p: Periodo, hoje=None):
    """Retorna o ano corrente se ele estiver dentro do período; senão None."""
    y = _ano(hoje)
    return y if p.ini <= y <= p.fim else None


def anos_faltantes(disponiveis, pedidos) -> list:
    return sorted(set(pedidos) - set(int(a) for a in disponiveis))


def filtrar_por_ano(obj, p: Periodo, incluir_parcial=False, hoje=None):
    """Filtra Series/DataFrame cujo índice é o ano (int)."""
    y = _ano(hoje)
    idx = pd.Index(obj.index).astype(int)
    mask = (idx >= p.ini) & (idx <= p.fim)
    if not incluir_parcial:
        mask &= idx < y
    return obj[mask]


def descrever(p: Periodo, hoje=None) -> str:
    comp = anos_completos(p, hoje)
    parc = ano_parcial_no_periodo(p, hoje)
    partes = []
    if comp:
        partes.append(f"{len(comp)} ano(s) completo(s): {comp[0]}–{comp[-1]}" if len(comp) > 1
                      else f"1 ano completo: {comp[0]}")
    if parc:
        partes.append(f"{parc} é parcial (ano em andamento)")
    return " · ".join(partes) if partes else "Nenhum ano completo no período"


def rotulo_trimestre(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"{(ts.month - 1) // 3 + 1}T{ts.year % 100:02d}"
