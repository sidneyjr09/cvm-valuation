"""Tests for cvm_valuation.balance."""
import io
import zipfile

import pandas as pd

from cvm_valuation.balance import (
    build_balance_history,
    build_balance_table,
    find_cash,
    find_debt,
)


def test_cash_sums_cash_and_short_term_investments(make_statement):
    assets = make_statement([
        {"CD_CONTA": "1.01", "VL_CONTA": 1000.0},
        {"CD_CONTA": "1.01.01", "VL_CONTA": 300.0},
        {"CD_CONTA": "1.01.02", "VL_CONTA": 50.0},
        {"CD_CONTA": "1.02.01.01", "VL_CONTA": 999.0},  # long-term: not cash
    ])
    assert find_cash(assets) == 350.0


def test_cash_missing_account_is_nan(make_statement):
    assets = make_statement([{"CD_CONTA": "1.01.01", "VL_CONTA": 300.0}])
    assert pd.isna(find_cash(assets))


def test_debt_includes_loans_and_leases_only(make_statement):
    # Lines modeled on Vivara's 2025 balance sheet
    liabilities = make_statement([
        {"CD_CONTA": "2.01.04", "DS_CONTA": "Empréstimos e Financiamentos", "VL_CONTA": 200.0},
        {"CD_CONTA": "2.02.01", "DS_CONTA": "Empréstimos e Financiamentos", "VL_CONTA": 300.0},
        {"CD_CONTA": "2.01.05", "DS_CONTA": "Outras Obrigações", "VL_CONTA": 75.0},
        {"CD_CONTA": "2.01.05.02", "DS_CONTA": "Outros", "VL_CONTA": 75.0},
        {"CD_CONTA": "2.01.05.02.01", "DS_CONTA": "Dividendos e JCP a Pagar", "VL_CONTA": 10.0},
        {"CD_CONTA": "2.01.05.02.04", "DS_CONTA": "Arrendamentos a pagar", "VL_CONTA": 15.0},
        {"CD_CONTA": "2.01.05.02.06", "DS_CONTA": "Instrumentos derivativos passivo", "VL_CONTA": 50.0},
        {"CD_CONTA": "2.02.02.02.04", "DS_CONTA": "Arrendamentos de direito de uso a pagar", "VL_CONTA": 600.0},
        {"CD_CONTA": "2.02.02.02.05", "DS_CONTA": "Passivo de Direito de Uso", "VL_CONTA": 5.0},
        {"CD_CONTA": "2.01.02", "DS_CONTA": "Fornecedores", "VL_CONTA": 999.0},
    ])
    # 200 + 300 (loans) + 15 + 600 + 5 (leases); totals, dividends,
    # derivatives and suppliers are not debt
    assert find_debt(liabilities) == 1120.0


def test_debt_without_leases(make_statement):
    liabilities = make_statement([
        {"CD_CONTA": "2.01.04", "VL_CONTA": 200.0},
        {"CD_CONTA": "2.02.01", "VL_CONTA": 300.0},
    ])
    assert find_debt(liabilities) == 500.0


def test_balance_table_computes_net_debt(make_statement):
    assets_data = {111: make_statement([
        {"CD_CONTA": "1.01.01", "VL_CONTA": 300.0},
        {"CD_CONTA": "1.01.02", "VL_CONTA": 50.0},
    ])}
    liabilities_data = {111: make_statement([
        {"CD_CONTA": "2.01.04", "VL_CONTA": 200.0},
        {"CD_CONTA": "2.02.01", "VL_CONTA": 300.0},
    ])}
    table = build_balance_table(assets_data, liabilities_data, 2025)
    assert list(table.columns) == ["CD_CVM", "YEAR", "DEBT", "CASH", "NET_DEBT"]
    row = table.iloc[0]
    assert row["DEBT"] == 500.0
    assert row["CASH"] == 350.0
    assert row["NET_DEBT"] == 150.0


def test_balance_table_company_without_assets_has_nan_cash(make_statement):
    liabilities_data = {111: make_statement([
        {"CD_CONTA": "2.01.04", "VL_CONTA": 200.0},
        {"CD_CONTA": "2.02.01", "VL_CONTA": 300.0},
    ])}
    table = build_balance_table({}, liabilities_data, 2025)
    assert pd.isna(table["CASH"].iloc[0])
    assert pd.isna(table["NET_DEBT"].iloc[0])


def test_balance_history_reads_both_statements(tmp_path, monkeypatch, make_statement):
    # Build a fake DFP zip with a BPA and a BPP file, saved in a temporary cache
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    assets = make_statement([
        {"CD_CONTA": "1.01.01", "VL_CONTA": 300.0},
        {"CD_CONTA": "1.01.02", "VL_CONTA": 50.0},
    ])
    liabilities = make_statement([
        {"CD_CONTA": "2.01.04", "VL_CONTA": 200.0},
        {"CD_CONTA": "2.02.01", "VL_CONTA": 300.0},
    ])
    with zipfile.ZipFile(tmp_path / "dfp_cia_aberta_2025.zip", "w") as z:
        z.writestr("dfp_cia_aberta_BPA_con_2025.csv",
                   assets.to_csv(sep=";", index=False).encode("latin-1"))
        z.writestr("dfp_cia_aberta_BPP_con_2025.csv",
                   liabilities.to_csv(sep=";", index=False).encode("latin-1"))
    history = build_balance_history({2025: "https://example.com/dfp_cia_aberta_2025.zip"})
    assert len(history) == 1
    assert history["NET_DEBT"].iloc[0] == 150.0
