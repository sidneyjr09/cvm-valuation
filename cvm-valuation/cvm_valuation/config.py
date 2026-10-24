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
EQUITY_ACCOUNT = "2.03"
OTHER_LIABILITIES = ("2.01.05.", "2.02.02.")
LEASE_TERMS = ["arrendament", "direito de uso"]
LEASE_KEYWORDS = "|".join(LEASE_TERMS)

FCA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/"
SHARE_TYPES = ["Ações Ordinárias", "Ações Preferenciais"]
TICKER_PATTERN = r"[A-Z][A-Z0-9]{3}\d{1,2}"

PRICE_PERIOD = "3mo"

# Some companies report their share count in thousands, with no column saying
# so. With the wrong scale, the price-to-book ratio falls below this floor.
MIN_PRICE_TO_BOOK = 0.05

# DCF assumptions (nominal, in reais). They drive the result: review them
# before reading any intrinsic value.
FCF_BASE_YEARS = 3
PROJECTION_YEARS = 5
GROWTH_RATE = 0.05
TERMINAL_GROWTH = 0.04
DISCOUNT_RATE = 0.15
