"""Catálogo de séries econômicas, setores e explicações (somente dados estáticos).

IMPORTANTE: códigos marcados com confianca="a confirmar" foram escritos de memória e NÃO foram
testados online. A aba Macroeconomia tem um botão "Testar fontes" que mostra o que funciona.
Nada aqui contém valores de mercado: só metadados. Valores sempre vêm das APIs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Serie:
    id: str
    nome: str
    grupo: str
    fonte: str          # texto exibido ao usuário
    tipo: str           # "sgs" (Banco Central) | "sidra" (IBGE) | "yf" (Yahoo Finance)
    ref: str            # código SGS, caminho SIDRA ou símbolo Yahoo
    unidade: str
    periodicidade: str  # "diaria" | "mensal" | "trimestral"
    var: str            # "pp" (variação em pontos) | "pct" (variação percentual)
    o_que_e: str
    impacto: str
    oficial: bool = True
    confianca: str = "alta"
    palavras: tuple = ()  # SIDRA: trechos do nome da variável a procurar


def _s(*a, **k):
    return Serie(*a, **k)


SIDRA_PIB = "t/5932/n1/all/v/all/p/all/c11255/90707"
SIDRA_PIM = "t/8888/n1/all/v/all/p/all/c544/129314"
SIDRA_PMC = "t/8880/n1/all/v/all/p/all/c11046/56734/c85/7169"
SIDRA_RENDA = "t/6390/n1/all/v/all/p/all"

_LISTA = [
    # ---- Juros e inflação
    _s("selic_meta", "Meta Selic", "Juros e inflação", "Banco Central (SGS 432)", "sgs", "432", "% a.a.",
       "diaria", "pp", "Taxa básica de juros definida pelo Copom. Referência para todos os juros da economia.",
       "Juros altos encarecem dívida e financiamento e tornam a renda fixa mais atraente que ações. "
       "Para bancos o efeito pode ser misto (receita de crédito x inadimplência)."),
    _s("selic_efetiva", "Selic efetiva (anualizada)", "Juros e inflação", "Banco Central (SGS 1178)", "sgs",
       "1178", "% a.a.", "diaria", "pp", "Taxa média que os bancos realmente praticam entre si, ao ano.",
       "Costuma andar muito perto da meta Selic; serve de conferência."),
    _s("ipca_mensal", "IPCA – variação mensal", "Juros e inflação", "Banco Central (SGS 433) / IBGE", "sgs",
       "433", "% no mês", "mensal", "pp", "Inflação oficial do mês: quanto os preços ao consumidor subiram.",
       "Inflação corrói o poder de compra (pressiona varejo) e influencia as decisões de juros."),
    _s("ipca_12m", "IPCA – acumulado em 12 meses", "Juros e inflação", "Banco Central (SGS 13522) / IBGE",
       "sgs", "13522", "% em 12 meses", "mensal", "pp", "Inflação oficial acumulada nos últimos 12 meses.",
       "Compare com a meta de inflação do país: inflação acima da meta tende a manter juros altos."),
    # ---- Câmbio
    _s("dolar", "Dólar comercial (venda)", "Câmbio", "Banco Central (SGS 1)", "sgs", "1", "R$ por US$",
       "diaria", "pct", "Quantos reais custa um dólar.",
       "Dólar alto favorece exportadoras (petróleo, mineração) e pressiona quem tem dívida ou insumos em dólar."),
    # ---- Atividade e PIB
    _s("pib_ano", "PIB – variação sobre o mesmo trimestre do ano anterior", "Atividade e PIB",
       "IBGE / SIDRA (tabela 5932)", "sidra", SIDRA_PIB, "%", "trimestral", "pp",
       "Quanto a economia cresceu (em volume) comparado ao mesmo trimestre do ano anterior.",
       "Crescimento tende a ajudar vendas e lucros, mas o efeito varia muito entre setores.",
       confianca="a confirmar", palavras=("igual trimestre", "mesmo trimestre")),
    _s("pib_4tri", "PIB – acumulado em quatro trimestres", "Atividade e PIB", "IBGE / SIDRA (tabela 5932)",
       "sidra", SIDRA_PIB, "%", "trimestral", "pp", "Crescimento do PIB somando os últimos quatro trimestres.",
       "Mostra a tendência de fundo, com menos ruído que o dado de um trimestre.",
       confianca="a confirmar", palavras=("quatro trimestres",)),
    _s("ibcbr", "IBC-Br (atividade econômica)", "Atividade e PIB", "Banco Central (SGS 24364)", "sgs",
       "24364", "índice (dessaz.)", "mensal", "pct", "Termômetro mensal da atividade, antecipa o PIB.",
       "Ajuda a ver, mês a mês, se a economia acelera ou desacelera.", confianca="a confirmar"),
    # ---- Crédito
    _s("credito_saldo", "Saldo da carteira de crédito (total)", "Crédito", "Banco Central (SGS 20539)", "sgs",
       "20539", "R$ milhões", "mensal", "pct", "Total emprestado pelo sistema financeiro.",
       "Mais crédito sustenta consumo e investimento e é a matéria-prima da receita dos bancos.",
       confianca="a confirmar"),
    _s("inadimplencia_total", "Inadimplência – crédito total", "Crédito", "Banco Central (SGS 21082)", "sgs",
       "21082", "% da carteira", "mensal", "pp", "Parcela dos empréstimos com atraso superior a 90 dias.",
       "Inadimplência alta eleva as perdas dos bancos e sinaliza aperto financeiro das famílias.",
       confianca="a confirmar"),
    _s("inadimplencia_pf", "Inadimplência – pessoas físicas", "Crédito", "Banco Central (SGS 21084)", "sgs",
       "21084", "% da carteira", "mensal", "pp", "Atrasos acima de 90 dias nos empréstimos às famílias.",
       "Relevante para bancos com muito crédito a pessoas físicas e para o varejo.", confianca="a confirmar"),
    _s("inadimplencia_pj", "Inadimplência – pessoas jurídicas", "Crédito", "Banco Central (SGS 21083)", "sgs",
       "21083", "% da carteira", "mensal", "pp", "Atrasos acima de 90 dias nos empréstimos às empresas.",
       "Indica a saúde financeira das empresas.", confianca="a confirmar"),
    _s("juros_credito", "Taxa média de juros do crédito (total)", "Crédito", "Banco Central (SGS 20714)",
       "sgs", "20714", "% a.a.", "mensal", "pp", "Juro médio cobrado nas operações de crédito.",
       "Juros do crédito altos reduzem a demanda por financiamento (imóveis, bens duráveis).",
       confianca="a confirmar"),
    # ---- Emprego e renda
    _s("desocupacao", "Taxa de desocupação (PNAD Contínua)", "Emprego e renda", "Banco Central (SGS 24369) / IBGE",
       "sgs", "24369", "% da força de trabalho", "mensal", "pp", "Percentual de pessoas sem trabalho que procuram emprego.",
       "Desemprego baixo costuma sustentar consumo; o efeito depende também da renda.", confianca="a confirmar"),
    _s("rendimento", "Rendimento médio real habitual", "Emprego e renda", "IBGE / SIDRA (tabela 6390)", "sidra",
       SIDRA_RENDA, "R$", "mensal", "pct", "Quanto os ocupados ganham em média, já descontada a inflação.",
       "Renda real maior tende a favorecer o consumo.", confianca="a confirmar",
       palavras=("rendimento médio real habitual", "rendimento médio mensal real")),
    # ---- Fiscal
    _s("divida_liquida", "Dívida líquida do setor público (% do PIB)", "Fiscal", "Banco Central (SGS 4513)",
       "sgs", "4513", "% do PIB", "mensal", "pp", "Quanto o setor público deve, descontados seus ativos, em proporção ao PIB.",
       "Dívida crescente pode pressionar juros longos e o risco-país.", confianca="a confirmar"),
    _s("divida_bruta", "Dívida bruta do governo geral (% do PIB)", "Fiscal", "Banco Central (SGS 13762)",
       "sgs", "13762", "% do PIB", "mensal", "pp", "Dívida total do governo geral em proporção ao PIB.",
       "Indicador acompanhado por agências de rating e investidores.", confianca="a confirmar"),
    _s("resultado_primario", "Resultado primário do setor público (mensal)", "Fiscal", "Banco Central (SGS 5793)",
       "sgs", "5793", "R$ milhões", "mensal", "pct", "Receitas menos despesas do governo, sem contar juros. Positivo = superávit.",
       "Déficits recorrentes elevam a dívida e podem pressionar juros.", confianca="a confirmar"),
    # ---- Setoriais
    _s("igpm", "IGP-M – variação mensal", "Preços setoriais", "Banco Central (SGS 189) / FGV", "sgs", "189",
       "% no mês", "mensal", "pp", "Índice de preços que combina atacado, consumidor e construção; reajusta muitos contratos.",
       "Reajusta aluguéis e contratos de concessões, como energia e saneamento."),
    _s("incc", "INCC – custo da construção (variação mensal)", "Preços setoriais", "Banco Central (SGS 192) / FGV",
       "sgs", "192", "% no mês", "mensal", "pp", "Mede a variação do custo de construir imóveis.",
       "Custo de obra maior comprime a margem das construtoras se não for repassado ao preço.",
       confianca="a confirmar"),
    _s("consumo_energia", "Consumo de energia elétrica – Brasil (total)", "Produção e consumo", "Banco Central (SGS 1406)",
       "sgs", "1406", "GWh", "mensal", "pct", "Quanto de energia elétrica o país consumiu no mês.",
       "Consumo maior sustenta o volume vendido pelas distribuidoras.", confianca="a confirmar"),
    _s("producao_industrial", "Produção industrial – indústria geral", "Produção e consumo", "IBGE / SIDRA (tabela 8888)",
       "sidra", SIDRA_PIM, "% vs. mesmo mês do ano anterior", "mensal", "pp", "Quanto a indústria produziu, em volume.",
       "Termômetro da demanda por energia, aço, minério e bens de capital.", confianca="a confirmar",
       palavras=("mesmo mês",)),
    _s("vendas_varejo", "Volume de vendas do varejo (PMC)", "Produção e consumo", "IBGE / SIDRA (tabela 8880)",
       "sidra", SIDRA_PMC, "% vs. mesmo mês do ano anterior", "mensal", "pp", "Variação do volume vendido pelo comércio varejista.",
       "Mostra a força do consumo que chega às lojas.", confianca="a confirmar", palavras=("mesmo mês",)),
    _s("brent", "Petróleo Brent (futuro)", "Commodities", "Yahoo Finance (BZ=F) – dado de mercado, não oficial",
       "yf", "BZ=F", "US$ por barril", "diaria", "pct", "Preço internacional de referência do petróleo.",
       "Preço do petróleo alto tende a elevar a receita de petroleiras, mas pesa nos custos de quem consome combustível.",
       oficial=False),
]

CATALOGO = {s.id: s for s in _LISTA}
GRUPOS_MACRO = ["Juros e inflação", "Câmbio", "Atividade e PIB", "Crédito", "Emprego e renda", "Fiscal"]

# ---------------------------------------------------------------- setores
SETORES = {
    "Bancos": {
        "indicadores": ["selic_meta", "credito_saldo", "inadimplencia_total", "inadimplencia_pf", "juros_credito", "ibcbr"],
        "porque": {
            "selic_meta": "Influencia o custo de captação e o retorno do crédito; juros muito altos também podem frear a demanda.",
            "credito_saldo": "Volume de crédito é a base da receita de juros dos bancos.",
            "inadimplencia_total": "Atrasos viram provisões (perdas) e reduzem o lucro.",
            "inadimplencia_pf": "Importante para bancos com carteira forte em pessoas físicas.",
            "juros_credito": "Mostra o preço do crédito cobrado dos clientes.",
            "ibcbr": "Atividade fraca costuma reduzir a procura por crédito e elevar riscos.",
        },
        "afeta": {"Receitas": "Volume de crédito e spread (diferença entre o que o banco cobra e paga).",
                  "Custos": "Provisões para devedores duvidosos e custo de captação.",
                  "Margens": "Podem variar com spread e inadimplência.",
                  "Riscos": "Inadimplência e desaceleração da economia."},
    },
    "Varejo": {
        "indicadores": ["ipca_12m", "desocupacao", "rendimento", "vendas_varejo", "selic_meta"],
        "porque": {
            "ipca_12m": "Inflação alta reduz o poder de compra, mas pode aumentar o preço médio praticado.",
            "desocupacao": "Mais gente empregada costuma significar mais consumo.",
            "rendimento": "Renda real é o que as famílias têm para gastar.",
            "vendas_varejo": "Mede diretamente o volume vendido pelo setor.",
            "selic_meta": "Juros altos encarecem o crediário e a dívida das próprias varejistas.",
        },
        "afeta": {"Receitas": "Consumo das famílias, renda e emprego.",
                  "Custos": "Preços de mercadorias, frete e despesas financeiras.",
                  "Margens": "Dependem de repassar (ou não) a inflação ao consumidor.",
                  "Riscos": "Endividamento das famílias e crédito mais caro."},
    },
    "Energia elétrica": {
        "indicadores": ["consumo_energia", "igpm", "ipca_12m", "selic_meta", "ibcbr"],
        "porque": {
            "consumo_energia": "Volume consumido sustenta a receita das distribuidoras e geradoras.",
            "igpm": "Muitos contratos e tarifas são reajustados por índices de preços como o IGP-M.",
            "ipca_12m": "Tarifas reguladas costumam ser corrigidas pela inflação.",
            "selic_meta": "Setor intensivo em capital e dívida; juros pesam nas despesas financeiras.",
            "ibcbr": "Atividade econômica influencia o consumo industrial e comercial.",
        },
        "afeta": {"Receitas": "Consumo e reajustes tarifários (regulados).",
                  "Custos": "Compra de energia, encargos e despesas financeiras.",
                  "Margens": "Em geral mais estáveis por regulação, mas dependem de cada concessão.",
                  "Riscos": "Regulação, hidrologia e endividamento."},
    },
    "Petróleo e gás": {
        "indicadores": ["brent", "dolar", "ibcbr", "selic_meta"],
        "porque": {
            "brent": "Preço internacional é o principal determinante da receita.",
            "dolar": "Receita atrelada ao dólar, enquanto parte dos custos é em reais.",
            "ibcbr": "Atividade influencia a demanda interna por combustíveis.",
            "selic_meta": "Afeta o custo de capital de investimentos longos.",
        },
        "afeta": {"Receitas": "Preço do barril, câmbio e volume produzido.",
                  "Custos": "Custos de extração, impostos e investimentos.",
                  "Margens": "Variam bastante com petróleo e câmbio.",
                  "Riscos": "Política de preços, regulação e volatilidade."},
        "limitacao": "Produção de petróleo (ANP) ainda não está integrada.",
    },
    "Mineração": {
        "indicadores": ["dolar", "producao_industrial", "ibcbr", "selic_meta"],
        "porque": {
            "dolar": "Vendas em dólar e custos em reais: câmbio mexe com a margem.",
            "producao_industrial": "Indústria (aço, construção) compra minério; sinal de demanda.",
            "ibcbr": "Atividade geral do país.",
            "selic_meta": "Custo de capital de projetos de longa duração.",
        },
        "afeta": {"Receitas": "Preço das commodities, câmbio e demanda externa (especialmente da China).",
                  "Custos": "Energia, combustíveis e logística.",
                  "Margens": "Sensíveis ao preço do minério e ao câmbio.",
                  "Riscos": "Preços internacionais, acidentes e regulação ambiental."},
        "limitacao": "Preço do minério de ferro e demanda externa ainda não estão integrados.",
    },
    "Indústria": {
        "indicadores": ["producao_industrial", "ibcbr", "dolar", "selic_meta", "igpm"],
        "porque": {
            "producao_industrial": "Mostra o ritmo do próprio setor.",
            "ibcbr": "Atividade econômica geral.",
            "dolar": "Afeta insumos importados e exportações.",
            "selic_meta": "Financiamento de máquinas e capital de giro.",
            "igpm": "Indicador de preços no atacado, ligado a custos de insumos.",
        },
        "afeta": {"Receitas": "Demanda interna e exportações.",
                  "Custos": "Insumos, energia, câmbio e salários.",
                  "Margens": "Dependem de repassar custos aos preços.",
                  "Riscos": "Ciclo econômico e concorrência externa."},
    },
    "Construção civil": {
        "indicadores": ["incc", "selic_meta", "credito_saldo", "ibcbr", "desocupacao"],
        "porque": {
            "incc": "Custo de construção pressiona a margem das obras.",
            "selic_meta": "Juros altos encarecem o financiamento imobiliário.",
            "credito_saldo": "Crédito disponível sustenta a compra de imóveis.",
            "ibcbr": "Atividade influencia a confiança para comprar imóveis.",
            "desocupacao": "Emprego e renda sustentam a demanda por moradia.",
        },
        "afeta": {"Receitas": "Lançamentos e vendas, ligadas a crédito e renda.",
                  "Custos": "Materiais, mão de obra e terrenos (INCC).",
                  "Margens": "Podem ser comprimidas se o custo subir mais que o preço de venda.",
                  "Riscos": "Juros, distratos e ciclo imobiliário."},
    },
}

# Alavancas do valuation: justificativa econômica por setor (texto). Sem texto = sem vínculo direto mapeado.
JUSTIFICATIVA_GERAL = {
    "taxa": "A taxa de desconto reflete o retorno exigido, que acompanha a taxa de juros (Selic) e o risco do país.",
}
JUSTIFICATIVA_SETOR = {
    "Bancos": {"lpa": "Inadimplência e volume de crédito afetam o lucro por ação.",
               "g": "Crescimento do crédito acompanha a atividade econômica."},
    "Varejo": {"lpa": "Consumo, renda e inflação afetam vendas e margens.",
               "g": "Renda e emprego influenciam o crescimento das vendas."},
    "Energia elétrica": {"g": "Consumo e reajustes tarifários influenciam o fluxo de caixa.",
                         "lpa": "Reajustes por IGP-M/IPCA e despesas financeiras afetam o lucro."},
    "Petróleo e gás": {"lpa": "Preço do petróleo e câmbio afetam o lucro.",
                       "div": "Dividendos seguem o caixa gerado, ligado ao petróleo e ao câmbio.",
                       "g": "Preço do petróleo e câmbio influenciam o fluxo de caixa."},
    "Mineração": {"lpa": "Câmbio e preços de commodities afetam o lucro.",
                  "div": "Dividendos seguem o caixa gerado.", "g": "Demanda externa influencia o fluxo de caixa."},
    "Indústria": {"lpa": "Demanda, câmbio e custos de insumos afetam o lucro.", "g": "Atividade industrial influencia o fluxo de caixa."},
    "Construção civil": {"lpa": "Custo de obra e crédito imobiliário afetam as margens.",
                         "g": "Juros e crédito influenciam lançamentos e vendas."},
}
JUSTIFICATIVA_YIELD = "O yield exigido pelo investidor tende a acompanhar a taxa de juros da renda fixa."

# Palavras-chave do Yahoo (sector/industry) -> setor do app, e tickers conhecidos (fallback)
_PALAVRAS = [
    ("bank", "Bancos"), ("credit services", "Bancos"), ("capital markets", "Bancos"),
    ("utilities", "Energia elétrica"), ("electric", "Energia elétrica"),
    ("oil", "Petróleo e gás"), ("gas", "Petróleo e gás"), ("energy", "Petróleo e gás"),
    ("mining", "Mineração"), ("steel", "Mineração"), ("metals", "Mineração"),
    ("residential construction", "Construção civil"), ("engineering", "Construção civil"),
    ("real estate", "Construção civil"), ("building", "Construção civil"),
    ("retail", "Varejo"), ("department stores", "Varejo"), ("grocery", "Varejo"), ("apparel", "Varejo"),
    ("industrial", "Indústria"), ("machinery", "Indústria"), ("electrical equipment", "Indústria"),
]
TICKERS_CONHECIDOS = {
    "ITUB4": "Bancos", "ITUB3": "Bancos", "BBDC4": "Bancos", "BBDC3": "Bancos", "BBAS3": "Bancos",
    "SANB11": "Bancos", "ITSA4": "Bancos", "BPAC11": "Bancos",
    "PETR4": "Petróleo e gás", "PETR3": "Petróleo e gás", "PRIO3": "Petróleo e gás", "RECV3": "Petróleo e gás",
    "VALE3": "Mineração", "CSNA3": "Mineração", "GGBR4": "Mineração", "USIM5": "Mineração",
    "ELET3": "Energia elétrica", "ELET6": "Energia elétrica", "CMIG4": "Energia elétrica",
    "EQTL3": "Energia elétrica", "TAEE11": "Energia elétrica", "CPLE6": "Energia elétrica", "EGIE3": "Energia elétrica",
    "MGLU3": "Varejo", "LREN3": "Varejo", "AMER3": "Varejo", "ASAI3": "Varejo", "RENT3": "Varejo",
    "WEGE3": "Indústria", "EMBR3": "Indústria", "SUZB3": "Indústria",
    "CYRE3": "Construção civil", "MRVE3": "Construção civil", "EZTC3": "Construção civil", "EVEN3": "Construção civil",
}


def mapear_setor(ticker: str, sector: str = None, industry: str = None):
    """Retorna (setor_do_app | None, origem). É uma SUGESTÃO; o usuário pode trocar."""
    if ticker in TICKERS_CONHECIDOS:
        return TICKERS_CONHECIDOS[ticker], "lista interna de tickers"
    txt = f"{industry or ''} {sector or ''}".lower()
    for chave, setor in _PALAVRAS:
        if chave in txt:
            return setor, "classificação do Yahoo Finance"
    return None, "não identificado"
