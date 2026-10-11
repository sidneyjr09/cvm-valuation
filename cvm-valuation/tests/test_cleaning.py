"""Tests for cvm_valuation.cleaning."""
from cvm_valuation.cleaning import split_by_company


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
