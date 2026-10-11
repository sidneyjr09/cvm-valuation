from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

DFP_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
CAD_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
CAPEX_TERMS = [
    "imobiliz",
    "intang",
    "software",
    "ativos? de contrato",
    "ativos? contratua",
    "infraestrutura",
    "ativos? da concess",
    "servi.o p.blico",
    "biol",
    "propriedades? para investimento",
]

EXCLUDE_TERMS = [
    "venda",
    "aliena",
    "baixa",
    "receb",
    "indeniza",
    "adiantamento",
    "transf",
    "decr.scimo",
]

CAPEX_KEYWORDS = "|".join(CAPEX_TERMS)
EXCLUDE_KEYWORDS = "|".join(EXCLUDE_TERMS)
FINANCIAL_SECTORS = [
    "Bancos",
    "Intermediação Financeira",
    "Crédito Imobiliário",
    "Arrendamento Mercantil",
    "Securitização de Recebíveis",
    "Factoring",
    "Seguradoras e Corretoras",
]
FINANCIAL_KEYWORDS = "|".join(FINANCIAL_SECTORS)