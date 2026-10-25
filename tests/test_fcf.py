"""Tests for cvm_valuation.fcf."""
import pandas as pd
import pytest

from cvm_valuation.fcf import build_fcf_table, find_capex, find_cfo


# find_cfo

def test_cfo_returns_account_value(make_statement):
    company = make_statement([{"CD_CONTA": "6.01", "VL_CONTA": 500.0}])
    assert find_cfo(company) == 500.0


def test_cfo_missing_account_returns_nan(make_statement):
    company = make_statement([{"CD_CONTA": "6.02", "VL_CONTA": -100.0}])
    assert pd.isna(find_cfo(company))


def test_cfo_repeated_account_raises_error(make_statement):
    company = make_statement([{"VL_CONTA": 500.0}, {"VL_CONTA": 300.0}])
    with pytest.raises(ValueError):
        find_cfo(company)


# find_capex

def test_capex_uses_only_capex_lines(make_statement):
    # One line of each kind found in the real data
    company = make_statement([
        {"CD_CONTA": "6.02", "DS_CONTA": "Caixa Líquido Atividades de Investimento", "VL_CONTA": -1000.0},
        {"CD_CONTA": "6.02.01", "DS_CONTA": "Aquisição de Imobilizado", "VL_CONTA": -300.0},
        {"CD_CONTA": "6.02.02", "DS_CONTA": "Aquisição de intangível", "VL_CONTA": -50.0},
        {"CD_CONTA": "6.02.03", "DS_CONTA": "Em ativos de contrato - infraestrutura", "VL_CONTA": -400.0},
        {"CD_CONTA": "6.02.04", "DS_CONTA": "Aumento em ativos biológicos", "VL_CONTA": -100.0},
        {"CD_CONTA": "6.02.05", "DS_CONTA": "Venda de imobilizado", "VL_CONTA": 20.0},
        {"CD_CONTA": "6.02.06", "DS_CONTA": "Adiantamentos nas operações de ativo biológico", "VL_CONTA": 500.0},
        {"CD_CONTA": "6.02.07", "DS_CONTA": "Aplicações financeiras", "VL_CONTA": -670.0},
    ])
    assert find_capex(company) == -850.0


def test_capex_ignores_case(make_statement):
    company = make_statement([
        {"CD_CONTA": "6.02.01", "DS_CONTA": "AQUISIÇÃO DE IMOBILIZADO", "VL_CONTA": -10.0},
    ])
    assert find_capex(company) == -10.0


def test_capex_without_capex_lines_is_zero(make_statement):
    company = make_statement([
        {"CD_CONTA": "6.02.01", "DS_CONTA": "Aplicações financeiras", "VL_CONTA": -10.0},
    ])
    assert find_capex(company) == 0.0


# build_fcf_table

def test_fcf_table_columns_and_values(make_statement):
    companies_data = {
        111: make_statement([
            {"CD_CONTA": "6.01", "VL_CONTA": 500.0},
            {"CD_CONTA": "6.02.01", "DS_CONTA": "Aquisição de imobilizado", "VL_CONTA": -200.0},
        ]),
    }
    table = build_fcf_table(companies_data, 2025)
    assert list(table.columns) == ["CD_CVM", "DENOM_CIA", "YEAR", "CFO", "CAPEX", "FCF"]
    row = table.iloc[0]
    assert row["CD_CVM"] == 111
    assert row["DENOM_CIA"] == "ALFA S.A."
    assert row["YEAR"] == 2025
    assert row["FCF"] == 300.0


def test_fcf_table_repeated_cfo_gives_nan_and_keeps_others(make_statement, capsys):
    companies_data = {
        111: make_statement([
            {"CD_CVM": 111, "CD_CONTA": "6.01", "VL_CONTA": 100.0},
            {"CD_CVM": 111, "CD_CONTA": "6.01", "VL_CONTA": 120.0},
        ]),
        222: make_statement([{"CD_CVM": 222, "CD_CONTA": "6.01", "VL_CONTA": 50.0}]),
    }
    table = build_fcf_table(companies_data, 2025).set_index("CD_CVM")
    assert pd.isna(table.loc[111, "CFO"])
    assert pd.isna(table.loc[111, "FCF"])
    assert table.loc[222, "CFO"] == 50.0
    assert "Company 111" in capsys.readouterr().out

