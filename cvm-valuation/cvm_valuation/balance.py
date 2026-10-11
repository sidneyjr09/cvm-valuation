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
    """Build a table with DEBT, CASH and NET_DEBT for each company in one year."""


def build_balance_history(dfp_links):
    """Build the balance sheet history of all companies."""