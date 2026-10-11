import pandas as pd

from .cleaning import split_by_company
from .config import CAPEX_KEYWORDS, EXCLUDE_KEYWORDS
from .sources import get_file, open_csv

def find_capex(company):
    """Return the total capex of one company.

    Values are in thousands of reais (negative = cash out).
    """
    investment = company[company["CD_CONTA"].str.startswith("6.02.")]
    is_asset = investment["DS_CONTA"].str.contains(CAPEX_KEYWORDS, case=False)
    is_sale = investment["DS_CONTA"].str.contains(EXCLUDE_KEYWORDS, case=False)
    capex = investment[is_asset & ~is_sale]
    return capex["VL_CONTA"].sum()

def find_cfo(company):
    """Return the operating cash flow (account 6.01) of one company.

    Values are in thousands of reais. Returns NaN if the account is
    missing and raises ValueError if it appears more than once.
    """
    is_cfo = company["CD_CONTA"] == "6.01"
    cfo = company[is_cfo]
    cfo_value = cfo["VL_CONTA"]
    if len(cfo_value) == 0:
        return float("nan")
    elif len(cfo_value) == 1:
        return cfo_value.iloc[0]
    else:
        code = company["CD_CVM"].iloc[0]
        raise ValueError(f"Company {code} has {len(cfo_value)} rows for account 6.01")

def build_fcf_table(companies_data, year):
    """Build a table with the free cash flow of each company in one year.

    Returns a DataFrame with one row per company and the columns
    CD_CVM, DENOM_CIA, YEAR, CFO, CAPEX and FCF. Values are in
    thousands of reais; FCF = CFO + CAPEX (capex is negative).
    """
    rows = []
    for code, group in companies_data.items():
        cfo = find_cfo(group)
        capex = find_capex(group)
        rows.append({
            "CD_CVM": code, "DENOM_CIA": group["DENOM_CIA"].iloc[0], "YEAR": year,
            "CFO": cfo, "CAPEX": capex, "FCF": cfo + capex})
    return pd.DataFrame(rows)

def build_fcf_history(dfp_links):
    """Build the free cash flow history of all companies.

    Takes a dictionary mapping each year to its DFP zip URL and returns
    a single DataFrame with one row per company and year, with the
    columns CD_CVM, DENOM_CIA, YEAR, CFO, CAPEX and FCF (in thousands
    of reais).
    """
    tables = []
    for year, link in dfp_links.items():
        print(f"Processing {year}...")
        zip_data = get_file(link)
        df = open_csv(zip_data, "DFC_MI", "con", year, "dfp")
        companies_data = split_by_company(df)
        fcf_table = build_fcf_table(companies_data, year)
        tables.append(fcf_table)
    return pd.concat(tables, ignore_index=True)