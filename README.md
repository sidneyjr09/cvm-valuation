# Investment Toolkit

Personal tools for monitoring asset prices and estimating the intrinsic value of stocks, built while learning Python and financial analysis.

| Module | What it does | Stack | Status |
|---|---|---|---|
| [`price-alerts`](price-alerts/) | Sends an email alert when an asset in a Google Sheets portfolio reaches a target price | Google Apps Script | Crypto alerts working; stocks and REITs in development |
| [`cvm-valuation`](cvm-valuation/) | Builds the free cash flow, net debt and share count history of Brazilian listed companies from CVM open data and values them with a DCF model | Python, pandas, pytest | Working end to end |

## Repository structure

```
investment-toolkit/
├── README.md
├── .gitignore
├── price-alerts/
│   ├── README.md
│   └── crypto_notification.gs
└── cvm-valuation/
    ├── pyproject.toml          # package definition (pip install -e .)
    ├── requirements.txt
    ├── cvm_valuation/          # the pipeline code
    │   ├── config.py           # paths, URLs, account codes, search terms, DCF assumptions
    │   ├── sources.py          # find, download (with cache) and read CVM files
    │   ├── cleaning.py         # clean a statement and split it by company
    │   ├── accounts.py         # read one account of a company
    │   ├── fcf.py              # operating cash flow, capex, FCF and history
    │   ├── balance.py          # debt (including leases), cash, net debt and equity
    │   ├── shares.py           # shares outstanding
    │   ├── registry.py         # company registry and flags
    │   ├── tickers.py          # stock tickers of each company
    │   ├── prices.py           # market prices and liquidity (Yahoo Finance)
    │   └── valuation.py        # DCF model, share scale fix, ranking and sensitivity
    ├── tests/                  # unit tests (pytest)
    ├── notebooks/
    │   ├── 01_fcf_history.ipynb  # builds the history and documents the data decisions
    │   ├── 02_valuation.ipynb    # tickers, prices, DCF and ranking
    │   └── 03_charts.ipynb       # charts of the FCF history
    └── data/                   # local cache of downloaded files (not versioned)
```

## Price alerts

A Google Apps Script bound to an investment spreadsheet. A time-driven trigger compares each asset's live quote (from `GOOGLEFINANCE`) with a target price and sends an HTML email when the target is reached. Each alert fires only once and is re-armed if the price falls back below the target.

Setup, spreadsheet layout and limitations are described in [`price-alerts/README.md`](price-alerts/README.md).

## CVM valuation

### Goal

Estimate the intrinsic value of Brazilian listed companies with a discounted cash flow (DCF) model, using historical data taken directly from regulatory filings instead of third-party data providers.

### Data sources

The CVM (Comissão de Valores Mobiliários, Brazil's securities regulator) publishes, on its [open data portal](https://dados.cvm.gov.br/):

| Source | File | Use |
|---|---|---|
| Annual financial statements (DFP), one zip per year since 2010 | `DFC_MI` (cash flow, indirect method) | Operating cash flow and capex |
| | `BPA` / `BPP` (balance sheet) | Cash, debt and net debt |
| | `composicao_capital` (share capital) | Shares outstanding |
| Company registry | `cad_cia_aberta.csv` | Sector, registration status and listing market |
| Registration form (FCA) | `valor_mobiliario` (securities) | Stock tickers |

Market prices come from Yahoo Finance, through the `yfinance` library.

### How the pipeline works

1. **Sources.** List the yearly zip files on the CVM website (web scraping), keep only years whose files are complete, download them with a local cache and read each statement.
2. **Cleaning.** Keep the latest fiscal year (`ÚLTIMO`), drop fully duplicated rows, convert values reported in units to thousands of reais, and keep only the most recent document of each company (latest `DT_REFER`, then latest `VERSAO`).
3. **Cash flow.** Operating cash flow is the standard account `6.01`. Capex has no standard account, so it is the sum of the lines in `6.02` whose description matches a list of capex terms (fixed and intangible assets, concession contract assets, biological assets, investment properties) and does not match a list of exclusion terms (sales, write-offs, advances). `FCF = CFO + CAPEX`, with capex negative.
4. **Net debt.** Gross debt is loans and debentures (`2.01.04`, `2.02.01`) plus the lease lines found by name in other liabilities; leases are treated as debt, as under IFRS 16. Cash is `1.01.01` + `1.01.02`.
5. **Shares.** Shares outstanding are the total shares issued minus treasury shares. The share capital file identifies companies only by CNPJ, so the CVM code is taken from the balance sheet of the same year.
6. **Registry.** Merge the company registry and flag financial companies (`IS_FINANCIAL`) and companies that can be analyzed and bought today (`IS_INVESTABLE`: active, category A, listed on the exchange, operating normally and not financial). Companies are flagged, not removed, to avoid survivorship bias in the history.
7. **Tickers and prices.** Take the common and preferred share tickers still traded on the exchange from the FCA, download three months of prices and keep, for each company, its most traded share class.
8. **Valuation.** Share counts reported in thousands are fixed first (price-to-book check). Then a two-stage DCF: the average FCF of the last three years grows for five years and then at a terminal rate; the enterprise value minus net debt, divided by shares outstanding, gives the intrinsic value per share, which is compared with the price.

The notebooks explain each decision with the real cases that motivated it.

### Results

- FCF and net debt history for **2010 to 2025**, with roughly 330 to 460 companies per year; share count from 2020.
- In the 2025 files: 427 companies with a cash flow statement, 279 listed on the exchange and **223 investable** after removing inactive, category B, non-operating and financial companies. These numbers may change slightly when the CVM republishes a file or updates the registry.
- Validation against company filings:
  - Cemig, 2025: the capex rule finds R$ 6.46 billion, against R$ 6.63 billion of "investimentos realizados" in the investor relations spreadsheet. The gap is expected, since the cash flow statement is on a cash basis and the release on an accrual basis.
  - Vivara, 2025: gross debt R$ 1.23 billion (more than half of it leases), cash R$ 0.40 billion, net debt R$ 0.83 billion and 235,071,814 shares outstanding.
- A ranking of the liquid investable companies by upside (intrinsic value / price − 1), with a sensitivity table for any company.

### Data quality findings

- Each zip repeats the previous year as a comparative (`ORDEM_EXERC = PENÚLTIMO`).
- Some files contain fully duplicated rows (320 in 2025).
- Values are reported either in thousands or in units (`ESCALA_MOEDA`).
- A company may have more than one document in the same file (Estrela filed a 3-month and a full-year DFP in 2011).
- The company registry repeats companies listed in more than one market.
- The share capital file only exists in the DFP zips from 2020 onwards, and identifies companies only by CNPJ.
- The share capital file has no scale column, and many companies report their share count in thousands (60 of the 193 companies valued in 2025, including Ambev, Vale and Cemig). These are detected by a price-to-book ratio below 0.05 and multiplied by 1,000.
- The FCA securities file includes debt securities, delisted tickers (BRFS3, after the BRF and Marfrig merger), units and invalid codes (`000000`, `NÃO HÁ`).

### Known limitations

- A few companies report capex with a positive sign; these cases should be reviewed by hand.
- Some companies seem to report a wrong `ESCALA_MOEDA`; values should be sanity-checked against company filings.
- Part of the capex of power transmission companies may be classified in operating activities.
- Only the indirect-method cash flow statement is used; companies that report with the direct method are missing.
- Since 2019 (IFRS 16), lease payments are classified as financing, so years before and after 2019 are not fully comparable.
- `YEAR` is the year of the CVM file; for companies with a non-calendar fiscal year, it refers to the fiscal year ending in that year.
- Capex is measured on a cash basis and may differ from the capex reported in earnings releases.
- The share count history starts in 2020; the valuation only needs the current one.
- The DCF uses the same assumptions (growth, discount rate) for every company, values common and preferred shares equally, and is driven by historical FCF. The ranking is a screen to find companies worth studying, not investment advice.

### Progress

- [x] List and download the yearly DFP files, with a local cache
- [x] Clean the statements (comparatives, duplicates, scale, multiple documents)
- [x] Identify capex lines and compute free cash flow
- [x] Build a multi-year history
- [x] Add the company registry and flag financial and investable companies
- [x] Organize the code as a Python package
- [x] Unit tests with pytest
- [x] Compute net debt (including leases)
- [x] Compute shares outstanding
- [x] Find tickers and market prices
- [x] Build the DCF model, the intrinsic value per share and a ranking
- [ ] Share count before 2020 (Formulário de Referência)
- [ ] Sector-specific DCF assumptions
- [ ] Use the intrinsic value as the ceiling price in `price-alerts`

### Setup

Requires Python 3.11 or later.

```bash
cd cvm-valuation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # makes the cvm_valuation package importable
pytest                           # runs the unit tests
```

Then open the notebooks in VS Code or Jupyter, selecting the `.venv` kernel, and run all cells:

1. `notebooks/01_fcf_history.ipynb` builds the history and saves it to `data/history_full.csv`. The first run downloads about 200 MB of CVM files into `data/`; later runs read them from disk. To refresh a year, delete its zip from `data/`.
2. `notebooks/02_valuation.ipynb` reads that table, finds tickers and prices and runs the DCF. The assumptions are in `config.py`.

The package can also be used directly:

```python
from cvm_valuation.config import DFP_URL
from cvm_valuation.sources import find_zips, complete_years
from cvm_valuation.fcf import build_fcf_history
from cvm_valuation.valuation import intrinsic_value

history = build_fcf_history(complete_years(find_zips(DFP_URL)))
intrinsic_value(base_fcf=150_000, net_debt=800_000, shares=235_000_000)   # reais per share
```

## Disclaimer

This is a personal study project. Nothing in this repository is investment advice.
