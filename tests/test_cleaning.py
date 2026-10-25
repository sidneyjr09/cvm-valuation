"""Tests for cvm_valuation.cleaning."""
from cvm_valuation.cleaning import pick_statement, split_by_company


def test_drops_comparative_year(make_statement):
    df = make_statement([
        {"ORDEM_EXERC": "PENÚLTIMO", "VL_CONTA": 80.0},
        {"ORDEM_EXERC": "ÚLTIMO", "VL_CONTA": 100.0},
    ])
    result = split_by_company(df)[111]
    assert len(result) == 1
    assert result["VL_CONTA"].iloc[0] == 100.0


def test_drops_duplicated_rows(make_statement):
    df = make_statement([{"VL_CONTA": 100.0}, {"VL_CONTA": 100.0}])
    assert len(split_by_company(df)[111]) == 1


def test_converts_units_to_thousands(make_statement):
    df = make_statement([{"ESCALA_MOEDA": "UNIDADE", "VL_CONTA": 7000.0}])
    result = split_by_company(df)[111]
    assert result["VL_CONTA"].iloc[0] == 7.0
    assert (result["ESCALA_MOEDA"] == "MIL").all()


def test_keeps_latest_document(make_statement):
    # Estrela (8427) filed a 3-month and a full-year DFP in 2011
    df = make_statement([
        {"DT_REFER": "2011-03-31", "VERSAO": 1, "VL_CONTA": 31004.0},
        {"DT_REFER": "2011-12-31", "VERSAO": 3, "VL_CONTA": 4664.0},
    ])
    result = split_by_company(df)[111]
    assert len(result) == 1
    assert result["VL_CONTA"].iloc[0] == 4664.0


def test_keeps_latest_version(make_statement):
    df = make_statement([
        {"VERSAO": 1, "VL_CONTA": 100.0},
        {"VERSAO": 2, "VL_CONTA": 120.0},
    ])
    result = split_by_company(df)[111]
    assert len(result) == 1
    assert result["VL_CONTA"].iloc[0] == 120.0


def test_latest_version_is_chosen_per_company(make_statement):
    df = make_statement([
        {"CD_CVM": 111, "VERSAO": 2, "VL_CONTA": 120.0},
        {"CD_CVM": 222, "VERSAO": 1, "VL_CONTA": 80.0},
    ])
    result = split_by_company(df)
    assert set(result) == {111, 222}
    assert result[222]["VL_CONTA"].iloc[0] == 80.0


def test_pick_statement_prefers_consolidated_with_values(make_statement):
    consolidated = make_statement([{"CD_CVM": 111, "VL_CONTA": 100.0}])
    individual = make_statement([{"CD_CVM": 111, "VL_CONTA": 90.0}])
    result = pick_statement(consolidated, individual)
    assert list(result["VL_CONTA"]) == [100.0]


def test_pick_statement_uses_individual_when_consolidated_is_all_zeros(make_statement):
    # TIM since 2024: the consolidated form is filled with zeros
    consolidated = make_statement([
        {"CD_CVM": 111, "CD_CONTA": "6.01", "VL_CONTA": 0.0},
        {"CD_CVM": 111, "CD_CONTA": "6.02", "VL_CONTA": 0.0},
    ])
    individual = make_statement([
        {"CD_CVM": 111, "CD_CONTA": "6.01", "VL_CONTA": 500.0},
        {"CD_CVM": 111, "CD_CONTA": "6.02", "VL_CONTA": -200.0},
    ])
    result = pick_statement(consolidated, individual)
    assert list(result["VL_CONTA"]) == [500.0, -200.0]


def test_pick_statement_adds_companies_with_only_individual(make_statement):
    consolidated = make_statement([{"CD_CVM": 111, "VL_CONTA": 100.0}])
    individual = make_statement([
        {"CD_CVM": 111, "VL_CONTA": 90.0},
        {"CD_CVM": 222, "VL_CONTA": 50.0},
    ])
    result = pick_statement(consolidated, individual)
    assert sorted(zip(result["CD_CVM"], result["VL_CONTA"])) == [(111, 100.0), (222, 50.0)]


def test_pick_statement_ignores_zeros_in_the_comparative_year(make_statement):
    # Only the latest year decides: zeros in the comparative column do not count
    consolidated = make_statement([
        {"CD_CVM": 111, "ORDEM_EXERC": "ÚLTIMO", "VL_CONTA": 100.0},
        {"CD_CVM": 111, "ORDEM_EXERC": "PENÚLTIMO", "VL_CONTA": 0.0},
    ])
    individual = make_statement([{"CD_CVM": 111, "VL_CONTA": 90.0}])
    result = pick_statement(consolidated, individual)
    assert 90.0 not in list(result["VL_CONTA"])


def test_account_with_two_start_dates_keeps_longest_period(make_statement):
    # TRV XLIII (26239) in 2023: the same document reports 6.01 from
    # 2023-01-21 and from 2023-01-01
    df = make_statement([
        {"DT_INI_EXERC": "2023-01-21", "CD_CONTA": "6.01", "VL_CONTA": -150.0},
        {"DT_INI_EXERC": "2023-01-01", "CD_CONTA": "6.01", "VL_CONTA": -200.0},
        {"DT_INI_EXERC": "2023-01-01", "CD_CONTA": "6.02", "VL_CONTA": -50.0},
    ])
    result = split_by_company(df)[111]
    assert sorted(zip(result["CD_CONTA"], result["VL_CONTA"])) == [("6.01", -200.0), ("6.02", -50.0)]


def test_balance_sheet_without_start_date_is_unchanged(make_statement):
    # BPA and BPP have no DT_INI_EXERC: a repeated account stays repeated,
    # so find_account can still report it
    df = make_statement([
        {"CD_CONTA": "1.01.01", "VL_CONTA": 10.0},
        {"CD_CONTA": "1.01.01", "VL_CONTA": 20.0},
    ])
    assert len(split_by_company(df)[111]) == 2

