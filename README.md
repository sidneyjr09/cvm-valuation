# Investment Toolkit

Personal tools for monitoring asset prices and estimating the intrinsic value of stocks, built while learning Python and financial analysis.

| Module | What it does | Stack | Status |
|---|---|---|---|
| [`price-alerts`](price-alerts/) | Sends an email alert when an asset in a Google Sheets portfolio reaches a target price | Google Apps Script | Crypto alerts working; stocks and REITs in development |
| [`cvm-valuation`](cvm-valuation/) | Extracts financial statements from CVM open data to estimate a stock's intrinsic value from its free cash flow | Python, pandas | In progress |

## Repository structure

```
investment-toolkit/
├── README.md
├── .gitignore
├── price-alerts/
│   ├── README.md
│   └── crypto_notification.gs
└── cvm-valuation/
    ├── requirements.txt
    ├── notebooks/
    │   └── cvm_data_miner.ipynb
    └── data/                  # local cache of downloaded files (not versioned)
```

## Price alerts

A Google Apps Script bound to an investment spreadsheet. A time-driven trigger compares each asset's live quote (from `GOOGLEFINANCE`) with a target price and sends an HTML email when the target is reached. Each alert fires only once and is re-armed if the price falls back below the target.

Setup, spreadsheet layout and limitations are described in [`price-alerts/README.md`](price-alerts/README.md).

## CVM valuation

### Goal

Estimate the intrinsic value of Brazilian listed companies with a discounted cash flow (DCF) model, using historical free cash flow taken directly from regulatory filings instead of third-party data providers.

### Data source

The CVM (Comissão de Valores Mobiliários, Brazil's securities regulator) publishes the standardized annual financial statements (DFP) of listed companies on its [open data portal](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp). There is one zip file per year since 2010, each containing one CSV per statement:

| File | Content | Use in the valuation |
|---|---|---|
| `DFC_MI` | Cash flow statement, indirect method | Operating cash flow and capex |
| `DRE` | Income statement | Revenue, EBIT, net income |
| `BPA` / `BPP` | Balance sheet (assets / liabilities and equity) | Cash and debt, for net debt |
| `composicao_capital` | Share capital composition | Share count, for value per share |

Each statement comes in a consolidated (`con`) and a parent-company-only (`ind`) version. The project uses the consolidated version, which covers the whole group.

### Progress

- [x] List the yearly zip files from the CVM directory page (web scraping with BeautifulSoup)
- [x] Download a zip file into memory
- [x] Read a statement CSV into a pandas DataFrame
- [ ] Filter a company and its latest fiscal year
- [ ] Identify capex lines and compute free cash flow
- [ ] Build a multi-year history
- [ ] Compute net debt and share count
- [ ] Build the DCF model and the intrinsic value per share

### Data caveats

- Each zip repeats the previous year as a comparative (`ORDEM_EXERC = PENÚLTIMO`). Only `ÚLTIMO` rows are kept, to avoid duplicates.
- Companies may restate a filing; when several `VERSAO` values exist, the latest one is used.
- Values are reported either in thousands or in units (`ESCALA_MOEDA`) and must be normalized.
- Capex is not a standardized account: its lines under investing activities (account `6.02`) are named differently by each company.
- Banks and insurers use a different chart of accounts and are out of scope.

### Setup

```bash
cd cvm-valuation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then open `notebooks/cvm_data_miner.ipynb` in VS Code or Jupyter, selecting the `.venv` kernel. Requires Python 3.9 or later.

## Disclaimer

This is a personal study project. Nothing in this repository is investment advice.