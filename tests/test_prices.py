import pandas as pd
import pytest

from cvm_valuation import prices
from cvm_valuation.prices import fetch_market_data, pick_main_ticker


def fake_download(close, volume):
    """Return a function that mimics yf.download with the given daily data."""
    def _download(symbols, **kwargs):
        data = pd.concat({"Close": pd.DataFrame(close), "Volume": pd.DataFrame(volume)}, axis=1)
        return data[[(field, symbol) for field in ["Close", "Volume"] for symbol in symbols]]
    return _download


def test_market_data_uses_last_close_and_average_traded_value(monkeypatch):
    close = {"ALFA3.SA": [10.0, 11.0, 12.0], "ALFA4.SA": [5.0, 5.0, float("nan")]}
    volume = {"ALFA3.SA": [100, 100, 100], "ALFA4.SA": [10, 30, float("nan")]}
    monkeypatch.setattr(prices.yf, "download", fake_download(close, volume))
    result = fetch_market_data(["ALFA3", "ALFA4"])
    assert list(result.columns) == ["TICKER", "PRICE", "AVG_TRADED_VALUE"]
    alfa3 = result[result["TICKER"] == "ALFA3"].iloc[0]
    alfa4 = result[result["TICKER"] == "ALFA4"].iloc[0]
    assert alfa3["PRICE"] == 12.0
    assert alfa3["AVG_TRADED_VALUE"] == pytest.approx(1100.0)
    assert alfa4["PRICE"] == 5.0              # the last day without data is skipped
    assert alfa4["AVG_TRADED_VALUE"] == pytest.approx(100.0)


def test_market_data_ticker_without_data_is_nan(monkeypatch):
    close = {"ALFA3.SA": [float("nan"), float("nan")]}
    volume = {"ALFA3.SA": [float("nan"), float("nan")]}
    monkeypatch.setattr(prices.yf, "download", fake_download(close, volume))
    result = fetch_market_data(["ALFA3"])
    assert pd.isna(result["PRICE"].iloc[0])


def test_main_ticker_is_the_most_traded():
    tickers = pd.DataFrame({
        "CD_CVM": [111, 111, 222],
        "TICKER": ["ALFA3", "ALFA4", "BETA3"],
        "SHARE_TYPE": ["Ações Ordinárias", "Ações Preferenciais", "Ações Ordinárias"],
    })
    market = pd.DataFrame({
        "TICKER": ["ALFA3", "ALFA4", "BETA3"],
        "PRICE": [10.0, 9.0, 20.0],
        "AVG_TRADED_VALUE": [1_000.0, 50_000.0, 500.0],
    })
    result = pick_main_ticker(tickers, market).sort_values("CD_CVM")
    assert list(result["TICKER"]) == ["ALFA4", "BETA3"]


def test_main_ticker_skips_tickers_without_price():
    tickers = pd.DataFrame({"CD_CVM": [111, 111], "TICKER": ["ALFA3", "ALFA4"], "SHARE_TYPE": ["", ""]})
    market = pd.DataFrame({
        "TICKER": ["ALFA3", "ALFA4"],
        "PRICE": [10.0, float("nan")],
        "AVG_TRADED_VALUE": [100.0, float("nan")],
    })
    assert list(pick_main_ticker(tickers, market)["TICKER"]) == ["ALFA3"]
