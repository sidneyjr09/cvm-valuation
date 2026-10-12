import pandas as pd

from .accounts import find_account
from .cleaning import split_by_company
from .config import CASH_ACCOUNTS, DEBT_ACCOUNTS, LEASE_KEYWORDS, OTHER_LIABILITIES
from .sources import get_file, open_csv


def find_debt(liabilities):
    """Return the gross debt of one company: loans, debentures and leases.

    Values are in thousands of reais.
    """
    loans = sum([find_account(liabilities, code) for code in DEBT_ACCOUNTS])
    other = liabilities[liabilities["CD_CONTA"].str.startswith(OTHER_LIABILITIES)]
    is_lease = other["DS_CONTA"].str.contains(LEASE_KEYWORDS, case=False)
    leases = other[is_lease]["VL_CONTA"].sum()
    return loans + leases


def find_cash(assets):
    """Return cash, cash equivalents and short-term financial investments.

    Values are in thousands of reais.
    """
    return sum([find_account(assets, code) for code in CASH_ACCOUNTS])


def build_balance_table(assets_data, liabilities_data, year):
    """Build a table with DEBT, CASH and NET_DEBT for each company in one year.

    Values are in thousands of reais; NET_DEBT = DEBT - CASH.
    """
    rows = []
    for code, liabilities in liabilities_data.items():
        assets = assets_data.get(code)
        debt = find_debt(liabilities)
        cash = find_cash(assets) if assets is not None else float("nan")
        rows.append({
            "CD_CVM": code, "YEAR": year,
            "DEBT": debt, "CASH": cash, "NET_DEBT": debt - cash})
    return pd.DataFrame(rows)


def build_balance_history(dfp_links):
    """Build the balance sheet history of all companies.

    Takes a dictionary mapping each year to its DFP zip URL and returns
    a single DataFrame with one row per company and year, with the
    columns CD_CVM, YEAR, DEBT, CASH and NET_DEBT (in thousands of reais).
    """
    tables = []
    for year, link in dfp_links.items():
        print(f"Processing {year}...")
        zip_data = get_file(link)
        assets_data = split_by_company(open_csv(zip_data, "BPA", "con", year, "dfp"))
        liabilities_data = split_by_company(open_csv(zip_data, "BPP", "con", year, "dfp"))
        balance_table = build_balance_table(assets_data, liabilities_data, year)
        tables.append(balance_table)
    return pd.concat(tables, ignore_index=True)