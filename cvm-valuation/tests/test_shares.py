import zipfile

import pandas as pd

from cvm_valuation.shares import build_shares_history, prepare_shares


def make_shares(rows):
    """Build a small share capital table; missing columns get default values."""
    defaults = {
        "CNPJ_CIA": "11.111.111/0001-11",
        "DT_REFER": "2025-12-31",
        "VERSAO": 1,
        "DENOM_CIA": "ALFA S.A.",
        "QT_ACAO_ORDIN_CAP_INTEGR": 0,
        "QT_ACAO_PREF_CAP_INTEGR": 0,
        "QT_ACAO_TOTAL_CAP_INTEGR": 0,
        "QT_ACAO_ORDIN_TESOURO": 0,
        "QT_ACAO_PREF_TESOURO": 0,
        "QT_ACAO_TOTAL_TESOURO": 0,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def write_zip(path, files):
    """Write a fake DFP zip with the given {file name: DataFrame} contents."""
    with zipfile.ZipFile(path, "w") as z:
        for name, df in files.items():
            z.writestr(name, df.to_csv(sep=";", index=False).encode("latin-1"))


def test_shares_subtracts_treasury():
    shares = make_shares([
        {"QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50},
    ])
    result = prepare_shares(shares)
    assert list(result.columns) == ["CNPJ_CIA", "SHARES"]
    assert result["SHARES"].iloc[0] == 950


def test_shares_keeps_latest_document():
    # Same company filed twice: an older document and a newer version
    shares = make_shares([
        {"VERSAO": 2, "QT_ACAO_TOTAL_CAP_INTEGR": 300},
        {"DT_REFER": "2025-03-31", "VERSAO": 3, "QT_ACAO_TOTAL_CAP_INTEGR": 100},
        {"VERSAO": 1, "QT_ACAO_TOTAL_CAP_INTEGR": 200},
    ])
    result = prepare_shares(shares)
    assert len(result) == 1
    assert result["SHARES"].iloc[0] == 300


def test_shares_one_row_per_company():
    shares = make_shares([
        {"CNPJ_CIA": "11.111.111/0001-11", "QT_ACAO_TOTAL_CAP_INTEGR": 100},
        {"CNPJ_CIA": "22.222.222/0001-22", "QT_ACAO_TOTAL_CAP_INTEGR": 200},
    ])
    result = prepare_shares(shares)
    assert sorted(result["SHARES"]) == [100, 200]


def test_shares_does_not_change_input():
    shares = make_shares([{"QT_ACAO_TOTAL_CAP_INTEGR": 100}])
    prepare_shares(shares)
    assert "SHARES" not in shares.columns


def test_shares_history_maps_cnpj_to_cvm_code(tmp_path, monkeypatch, make_statement):
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    shares = make_shares([
        {"QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50},
    ])
    # The BPP has one row per account, so the company appears more than once
    liabilities = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.02.01"},
    ])
    write_zip(tmp_path / "dfp_cia_aberta_2025.zip", {
        "dfp_cia_aberta_composicao_capital_2025.csv": shares,
        "dfp_cia_aberta_BPP_con_2025.csv": liabilities,
    })
    history = build_shares_history({2025: "https://example.com/dfp_cia_aberta_2025.zip"})
    assert list(history.columns) == ["CD_CVM", "YEAR", "SHARES"]
    assert len(history) == 1
    assert history["CD_CVM"].iloc[0] == 111
    assert history["SHARES"].iloc[0] == 950


def test_shares_history_skips_year_without_file(tmp_path, monkeypatch, make_statement):
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    liabilities = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
    ])
    shares = make_shares([{"QT_ACAO_TOTAL_CAP_INTEGR": 100}])
    # 2019 has no share capital file, 2025 has one
    write_zip(tmp_path / "dfp_cia_aberta_2019.zip", {
        "dfp_cia_aberta_BPP_con_2019.csv": liabilities,
    })
    write_zip(tmp_path / "dfp_cia_aberta_2025.zip", {
        "dfp_cia_aberta_composicao_capital_2025.csv": shares,
        "dfp_cia_aberta_BPP_con_2025.csv": liabilities,
    })
    history = build_shares_history({
        2019: "https://example.com/dfp_cia_aberta_2019.zip",
        2025: "https://example.com/dfp_cia_aberta_2025.zip",
    })
    assert list(history["YEAR"]) == [2025]


def test_shares_history_drops_company_without_balance_sheet(tmp_path, monkeypatch, make_statement):
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    shares = make_shares([
        {"CNPJ_CIA": "11.111.111/0001-11", "QT_ACAO_TOTAL_CAP_INTEGR": 100},
        {"CNPJ_CIA": "99.999.999/0001-99", "QT_ACAO_TOTAL_CAP_INTEGR": 500},
    ])
    liabilities = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
    ])
    write_zip(tmp_path / "dfp_cia_aberta_2025.zip", {
        "dfp_cia_aberta_composicao_capital_2025.csv": shares,
        "dfp_cia_aberta_BPP_con_2025.csv": liabilities,
    })
    history = build_shares_history({2025: "https://example.com/dfp_cia_aberta_2025.zip"})
    assert list(history["CD_CVM"]) == [111]
