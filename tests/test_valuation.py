import math

import pandas as pd
import pytest

from cvm_valuation.valuation import build_valuation, fix_share_scale, intrinsic_value, sensitivity_table


def test_intrinsic_value_no_growth_is_a_perpetuity():
    # With no growth at all, the DCF is a perpetuity: FCF / r = 100 / 0.10 = 1000
    # Equity = 1000 - 200 = 800 thousand reais, over 100 shares = 8,000 reais per share
    value = intrinsic_value(100, 200, 100, growth=0, terminal_growth=0, discount_rate=0.10, years=5)
    assert value == pytest.approx(8000)


def test_intrinsic_value_two_stage():
    # One year at 10% growth, then 0%: FCF1 = 110, PV = 110 / 1.1 + (110 / 0.1) / 1.1 = 1100
    value = intrinsic_value(100, 0, 1000, growth=0.10, terminal_growth=0, discount_rate=0.10, years=1)
    assert value == pytest.approx(1100)


@pytest.mark.parametrize("base_fcf, net_debt, shares", [
    (-50, 0, 100),               # negative FCF
    (0, 0, 100),                 # zero FCF
    (100, 0, 0),                 # no shares
    (float("nan"), 0, 100),      # missing FCF
    (100, float("nan"), 100),    # missing net debt
    (100, 0, float("nan")),      # missing shares
])
def test_intrinsic_value_not_meaningful_is_nan(base_fcf, net_debt, shares):
    assert math.isnan(intrinsic_value(base_fcf, net_debt, shares))


def test_intrinsic_value_rejects_discount_rate_below_terminal_growth():
    with pytest.raises(ValueError, match="discount_rate"):
        intrinsic_value(100, 0, 100, terminal_growth=0.05, discount_rate=0.05)


def make_history(rows):
    defaults = {"CD_CVM": 111, "DENOM_CIA": "ALFA S.A.", "YEAR": 2025, "FCF": 100.0,
                "NET_DEBT": 0.0, "EQUITY": 5.0, "SHARES": 1000.0, "IS_INVESTABLE": True}
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_valuation_uses_average_fcf_and_latest_balance_sheet():
    history = make_history([
        {"YEAR": 2022, "FCF": 1000.0, "NET_DEBT": 999.0},    # outside the 3-year window
        {"YEAR": 2023, "FCF": 50.0},
        {"YEAR": 2024, "FCF": 100.0},
        {"YEAR": 2025, "FCF": 150.0, "NET_DEBT": 20.0, "SHARES": 500.0},
    ])
    market = pd.DataFrame({"CD_CVM": [111], "TICKER": ["ALFA3"], "PRICE": [10.0], "AVG_TRADED_VALUE": [1.0]})
    result = build_valuation(history, market)
    row = result.iloc[0]
    assert row["BASE_FCF"] == pytest.approx(100.0)
    assert row["NET_DEBT"] == 20.0
    assert row["INTRINSIC_VALUE"] == pytest.approx(intrinsic_value(100.0, 20.0, 500.0))
    assert row["UPSIDE"] == pytest.approx(row["INTRINSIC_VALUE"] / 10.0 - 1)


def test_valuation_needs_fcf_in_every_base_year():
    history = make_history([{"YEAR": 2024}, {"YEAR": 2025}])    # 2023 is missing
    market = pd.DataFrame({"CD_CVM": [111], "TICKER": ["ALFA3"], "PRICE": [10.0], "AVG_TRADED_VALUE": [1.0]})
    result = build_valuation(history, market)
    assert math.isnan(result["BASE_FCF"].iloc[0])
    assert math.isnan(result["INTRINSIC_VALUE"].iloc[0])


def test_valuation_keeps_only_investable_companies_with_price():
    history = make_history([
        {"CD_CVM": 111, "YEAR": year} for year in [2023, 2024, 2025]
    ] + [
        {"CD_CVM": 222, "YEAR": year, "IS_INVESTABLE": False} for year in [2023, 2024, 2025]
    ] + [
        {"CD_CVM": 333, "YEAR": year} for year in [2023, 2024, 2025]
    ])
    market = pd.DataFrame({"CD_CVM": [111, 222], "TICKER": ["ALFA3", "BETA3"],
                           "PRICE": [10.0, 10.0], "AVG_TRADED_VALUE": [1.0, 1.0]})
    result = build_valuation(history, market)
    assert list(result["CD_CVM"]) == [111]


def test_sensitivity_table_shape_and_values():
    table = sensitivity_table(100, 0, 1000, discount_rates=[0.12, 0.15], growth_rates=[0.0, 0.05])
    assert list(table.index) == ["r=12%", "r=15%"]
    assert list(table.columns) == ["g=0%", "g=5%"]
    assert table.loc["r=15%", "g=5%"] == pytest.approx(intrinsic_value(100, 0, 1000))
    assert table.loc["r=12%", "g=5%"] > table.loc["r=15%", "g=5%"]


def test_share_scale_fixes_counts_in_thousands():
    # Price 10, equity 1,000 thousand reais (R$ 1 million)
    # 100,000 shares -> market value R$ 1 million, price-to-book 1: correct
    # 100 shares -> market value R$ 1,000, price-to-book 0.001: in thousands
    table = pd.DataFrame({
        "PRICE": [10.0, 10.0],
        "SHARES": [100_000.0, 100.0],
        "EQUITY": [1000.0, 1000.0],
    })
    result = fix_share_scale(table)
    assert list(result["SHARES"]) == [100_000.0, 100_000.0]
    assert list(result["SHARES_FIXED"]) == [False, True]
    assert result["PRICE_TO_BOOK"].tolist() == pytest.approx([1.0, 1.0])
    assert list(table["SHARES"]) == [100_000.0, 100.0]     # the input is not changed


def test_share_scale_skips_negative_or_missing_equity():
    table = pd.DataFrame({
        "PRICE": [10.0, 10.0],
        "SHARES": [100.0, 100.0],
        "EQUITY": [-1000.0, float("nan")],
    })
    result = fix_share_scale(table)
    assert list(result["SHARES"]) == [100.0, 100.0]
    assert not result["SHARES_FIXED"].any()


def test_valuation_fixes_share_scale_before_valuing():
    history = make_history([
        {"YEAR": year, "FCF": 100.0, "EQUITY": 1000.0, "SHARES": 100.0} for year in [2023, 2024, 2025]
    ])
    market = pd.DataFrame({"CD_CVM": [111], "TICKER": ["ALFA3"], "PRICE": [10.0], "AVG_TRADED_VALUE": [1.0]})
    row = build_valuation(history, market).iloc[0]
    assert row["SHARES"] == 100_000.0
    assert row["SHARES_FIXED"]
    assert row["INTRINSIC_VALUE"] == pytest.approx(intrinsic_value(100.0, 0.0, 100_000.0))
