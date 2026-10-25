import zipfile

import pandas as pd

from cvm_valuation.tickers import build_tickers, prepare_tickers


def make_securities(rows):
    """Build a small FCA securities table; missing columns get default values."""
    defaults = {
        "CNPJ_Companhia": "11.111.111/0001-11",
        "Valor_Mobiliario": "Ações Ordinárias",
        "Codigo_Negociacao": "ALFA3",
        "Mercado": "Bolsa",
        "Data_Fim_Negociacao": None,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_tickers_keeps_listed_common_and_preferred_shares():
    securities = make_securities([
        {"Codigo_Negociacao": "ALFA3"},
        {"Codigo_Negociacao": "ALFA4", "Valor_Mobiliario": "Ações Preferenciais"},
        {"Codigo_Negociacao": None, "Valor_Mobiliario": "Debêntures", "Mercado": "Balcão Organizado"},
        {"Codigo_Negociacao": "ALFA11", "Valor_Mobiliario": "Units"},
        {"Codigo_Negociacao": "ALFA5", "Mercado": "Balcão Organizado"},
    ])
    result = prepare_tickers(securities)
    assert list(result.columns) == ["CNPJ_CIA", "TICKER", "Valor_Mobiliario"]
    assert list(result["TICKER"]) == ["ALFA3", "ALFA4"]


def test_tickers_drops_tickers_no_longer_traded():
    securities = make_securities([
        {"Codigo_Negociacao": "ALFA3", "Data_Fim_Negociacao": "2025-09-22"},
        {"Codigo_Negociacao": "ALFA4", "Valor_Mobiliario": "Ações Preferenciais"},
    ])
    assert list(prepare_tickers(securities)["TICKER"]) == ["ALFA4"]


def test_tickers_drops_invalid_codes():
    securities = make_securities([
        {"Codigo_Negociacao": code}
        for code in ["000000", "RBNS", "NÃO HÁ", "PNC", "CPTP3B", "B3SA3", "TAEE11"]
    ])
    assert list(prepare_tickers(securities)["TICKER"]) == ["B3SA3", "TAEE11"]


def test_tickers_drops_repeated_rows():
    securities = make_securities([{"Codigo_Negociacao": "ALFA3"}, {"Codigo_Negociacao": "ALFA3"}])
    assert len(prepare_tickers(securities)) == 1


def test_build_tickers_uses_latest_files_and_maps_cvm_code(tmp_path, monkeypatch, make_statement):
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    securities = make_securities([
        {"Codigo_Negociacao": "ALFA3"},
        {"CNPJ_Companhia": "99.999.999/0001-99", "Codigo_Negociacao": "ZETA3"},
    ])
    liabilities = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.02.01"},
    ])
    with zipfile.ZipFile(tmp_path / "fca_cia_aberta_2026.zip", "w") as z:
        z.writestr("fca_cia_aberta_valor_mobiliario_2026.csv",
                   securities.to_csv(sep=";", index=False).encode("latin-1"))
    with zipfile.ZipFile(tmp_path / "dfp_cia_aberta_2025.zip", "w") as z:
        z.writestr("dfp_cia_aberta_BPP_con_2025.csv",
                   liabilities.to_csv(sep=";", index=False).encode("latin-1"))
    fca_links = {
        2025: "https://example.com/fca_cia_aberta_2025.zip",   # not in the cache: must not be used
        2026: "https://example.com/fca_cia_aberta_2026.zip",
    }
    dfp_links = {2025: "https://example.com/dfp_cia_aberta_2025.zip"}
    result = build_tickers(fca_links, dfp_links)
    assert list(result.columns) == ["CD_CVM", "TICKER", "SHARE_TYPE"]
    assert list(result["TICKER"]) == ["ALFA3"]
    assert result["CD_CVM"].iloc[0] == 111
