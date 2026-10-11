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

DEBT_ACCOUNTS = ["2.01.04", "2.02.01"]
CASH_ACCOUNTS = ["1.01.01", "1.01.02"]
OTHER_LIABILITIES = ("2.01.05.", "2.02.02.")
LEASE_TERMS = ["arrendament", "direito de uso"]
LEASE_KEYWORDS = "|".join(LEASE_TERMS)