# Investment Toolkit

Personal tools for monitoring asset prices and estimating the intrinsic value of stocks, built while learning Python and financial analysis.

| Module | What it does | Stack | Status |
|---|---|---|---|
| [`price-alerts`](price-alerts/) | Sends an email alert when an asset in a Google Sheets portfolio reaches a target price | Google Apps Script | Crypto alerts working; stocks and REITs in development |
| [`cvm-valuation`](cvm-valuation/) | Builds the free cash flow history of Brazilian listed companies from CVM open data, as the base for a DCF valuation | Python, pandas | FCF history done; valuation in progress |

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
    │   ├── config.py           # paths, URLs, capex terms, financial sectors
    │   ├── sources.py          # find, download (with cache) and read CVM files
    │   ├── cleaning.py         # clean a statement and split it by company
    │   ├── fcf.py              # operating cash flow, capex, FCF and history
    │   └── registry.py         # company registry and flags
    ├── notebooks/
    │   └── 01_fcf_history.ipynb  # runs the pipeline and documents the decisions
    └── data/                   # local cache of downloaded files (not versioned)
```

## Price alerts

A Google Apps Script bound to an investment spreadsheet. A time-driven trigger compares each asset's live quote (from `GOOGLEFINANCE`) with a target price and sends an HTML email when the target is reached. Each alert fires only once and is re-armed if the price falls back below the target.

Setup, spreadsheet layout and limitations are described in [`price-alerts/README.md`](price-alerts/README.md).

## CVM valuation

### Goal

Estimate the intrinsic value of Brazilian listed companies with a discounted cash flow (DCF) model, using historical free cash flow taken directly from regulatory filings instead of third-party data providers.

### Data sources

The CVM (Comissão de Valores Mobiliários, Brazil's securities regulator) publishes, on its [open data portal](https://dados.cvm.gov.br/):

- **The annual financial statements (DFP)**: one zip file per year since 2010, with one CSV per statement. The project currently uses the consolidated cash flow statement, indirect method (`DFC_MI`, `con`).
- **The company registry** (`cad_cia_aberta.csv`): sector, registration status and listing market of each company.

| File | Content | Use |
|---|---|---|
| `DFC_MI` | Cash flow statement, indirect method | Operating cash flow and capex (in use) |
| `BPA` / `BPP` | Balance sheet | Cash and debt, for net debt (next step) |
| `composicao_capital` | Share capital composition | Share count, for value per share (next step) |

### How the pipeline works

1. **Sources.** List the yearly DFP zip files on the CVM website (web scraping), keep only years whose files are complete, download them with a local cache and read the cash flow statement.
2. **Cleaning.** Keep the latest fiscal year (`ÚLTIMO`), drop fully duplicated rows, convert values reported in units to thousands of reais, and keep only the most recent document of each company (latest `DT_REFER`, then latest `VERSAO`).
3. **Metrics.** Operating cash flow is the standard account `6.01`. Capex has no standard account, so it is the sum of the lines in `6.02` whose description matches a list of capex terms (fixed and intangible assets, concession contract assets, biological assets, investment properties) and does not match a list of exclusion terms (sales, write-offs, advances). `FCF = CFO + CAPEX`, with capex negative.
4. **Registry.** Merge the company registry and flag financial companies (`IS_FINANCIAL`) and companies that can be analyzed and bought today (`IS_INVESTABLE`: active, category A, listed on the exchange, operating normally and not financial). Companies are flagged, not removed, to avoid survivorship bias in the history.

The notebook explains each decision with the real cases that motivated it.

### Results

- FCF history for **2010 to 2025**, with roughly 330 to 460 companies per year.
- In the 2025 files: 427 companies with a cash flow statement, 279 listed on the exchange and **223 investable** after removing inactive, category B, non-operating and financial companies. These numbers may change slightly when the CVM republishes a file or updates the registry.
- Validation: for Cemig in 2025, the capex rule finds R$ 6.46 billion, against R$ 6.63 billion of "investimentos realizados" in the company's investor relations spreadsheet. The gap is expected, since the cash flow statement is on a cash basis and the release on an accrual basis.

### Data quality findings

- Each zip repeats the previous year as a comparative (`ORDEM_EXERC = PENÚLTIMO`).
- Some files contain fully duplicated rows (320 in 2025).
- Values are reported either in thousands or in units (`ESCALA_MOEDA`).
- A company may have more than one document in the same file (Estrela filed a 3-month and a full-year DFP in 2011).
- The company registry repeats companies listed in more than one market.

### Known limitations

- A few companies report capex with a positive sign; these cases should be reviewed by hand.
- Some companies seem to report a wrong `ESCALA_MOEDA`; values should be sanity-checked against company filings.
- Part of the capex of power transmission companies may be classified in operating activities.
- Only the indirect-method cash flow statement is used; companies that report with the direct method are missing.
- Since 2019 (IFRS 16), lease payments are classified as financing, so years before and after 2019 are not fully comparable.
- `YEAR` is the year of the CVM file; for companies with a non-calendar fiscal year, it refers to the fiscal year ending in that year.
- Capex is measured on a cash basis and may differ from the capex reported in earnings releases.

### Progress

- [x] List and download the yearly DFP files, with a local cache
- [x] Clean the cash flow statement (comparatives, duplicates, scale, multiple documents)
- [x] Identify capex lines and compute free cash flow
- [x] Build a multi-year history
- [x] Add the company registry and flag financial and investable companies
- [x] Organize the code as a Python package
- [ ] Unit tests with pytest
- [ ] Compute net debt and share count
- [ ] Build the DCF model and the intrinsic value per share
- [ ] Use the intrinsic value as the ceiling price in `price-alerts`

### Setup

Requires Python 3.11 or later.

```bash
cd cvm-valuation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # makes the cvm_valuation package importable
```

Then open `notebooks/01_fcf_history.ipynb` in VS Code or Jupyter, selecting the `.venv` kernel, and run all cells. The first run downloads about 200 MB of CVM files into `data/`; later runs read them from disk. To refresh a year, delete its zip from `data/`.

The package can also be used directly:

```python
from cvm_valuation.config import DFP_URL
from cvm_valuation.sources import find_zips, complete_years
from cvm_valuation.fcf import build_fcf_history

history = build_fcf_history(complete_years(find_zips(DFP_URL)))
```

## Disclaimer

This is a personal study project. Nothing in this repository is investment advice.