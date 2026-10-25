import pandas as pd

from .cleaning import split_by_company
from .config import CAPEX_KEYWORDS, EXCLUDE_KEYWORDS
from .sources import get_file, open_statement
from .accounts import find_account

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
    return find_account(company, "6.01")

def build_fcf_table(companies_data, year):
    """Build a table with the free cash flow of each company in one year.

    Returns a DataFrame with one row per company and the columns
    CD_CVM, DENOM_CIA, YEAR, CFO, CAPEX and FCF. Values are in
    thousands of reais; FCF = CFO + CAPEX (capex is negative).

    A company whose operating cash flow appears more than once (a filing
    error) gets NaN instead of stopping the whole year, with a warning.
    """
    rows = []
    for code, group in companies_data.items():
        try:
            cfo = find_cfo(group)
        except ValueError as error:
            print(f"Warning ({year}): {error}. CFO and FCF set to NaN.")
            cfo = float("nan")
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
        df = open_statement(zip_data, "DFC_MI", year)
        companies_data = split_by_company(df)
        fcf_table = build_fcf_table(companies_data, year)
        tables.append(fcf_table)
    return pd.concat(tables, ignore_index=True)