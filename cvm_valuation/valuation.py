import pandas as pd

from .config import (
    DISCOUNT_RATE,
    FCF_BASE_YEARS,
    GROWTH_RATE,
    MIN_PRICE_TO_BOOK,
    PROJECTION_YEARS,
    TERMINAL_GROWTH,
)


def intrinsic_value(base_fcf, net_debt, shares, growth=GROWTH_RATE,
                    terminal_growth=TERMINAL_GROWTH, discount_rate=DISCOUNT_RATE,
                    years=PROJECTION_YEARS):
    """Return the intrinsic value per share of a company, in reais.

    A two-stage DCF: the base FCF grows at `growth` for `years` years,
    then at `terminal_growth` forever (Gordon growth). The enterprise
    value is the present value of these flows at `discount_rate`;
    the equity value is the enterprise value minus net debt.

    base_fcf and net_debt are in thousands of reais and shares is a
    number of shares. Returns NaN when the DCF is not meaningful: a
    missing input, a base FCF that is not positive or no shares.
    """
    if discount_rate <= terminal_growth:
        raise ValueError("discount_rate must be greater than terminal_growth")
    if pd.isna(base_fcf) or pd.isna(net_debt) or pd.isna(shares):
        return float("nan")
    if base_fcf <= 0 or shares <= 0:
        return float("nan")

    present_value = 0
    fcf = base_fcf
    for year in range(1, years + 1):
        fcf = fcf * (1 + growth)
        present_value += fcf / (1 + discount_rate) ** year

    terminal_value = fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    present_value += terminal_value / (1 + discount_rate) ** years

    equity_value = present_value - net_debt
    return equity_value * 1000 / shares


def fix_share_scale(table, min_price_to_book=MIN_PRICE_TO_BOOK):
    """Fix share counts reported in thousands instead of units.

    The share capital file has no scale column, and some companies (Ambev,
    Vale, Cemig...) report their share count in thousands. With 1,000 times
    fewer shares, the market value (price x shares) becomes tiny compared
    with the book value, so the price-to-book ratio falls far below any
    real value. Those share counts are multiplied by 1,000.

    Needs the columns PRICE, SHARES and EQUITY (thousands of reais). The
    check is only possible for companies with positive equity. Adds
    PRICE_TO_BOOK (after the fix) and SHARES_FIXED (True when fixed).
    """
    table = table.copy()
    market_value = table["PRICE"] * table["SHARES"] / 1000
    price_to_book = market_value / table["EQUITY"]
    is_thousands = (table["EQUITY"] > 0) & (price_to_book < min_price_to_book)
    table["SHARES"] = table["SHARES"].where(~is_thousands, table["SHARES"] * 1000)
    table["SHARES_FIXED"] = is_thousands
    table["PRICE_TO_BOOK"] = table["PRICE"] * table["SHARES"] / 1000 / table["EQUITY"]
    return table


def build_valuation(history_full, market, base_years=FCF_BASE_YEARS, growth=GROWTH_RATE,
                    terminal_growth=TERMINAL_GROWTH, discount_rate=DISCOUNT_RATE,
                    years=PROJECTION_YEARS, growth_by_company=None):
    """Compute the intrinsic value of every investable company.

    Uses the latest year of the history. The base FCF is the average FCF
    of the last `base_years` years, which smooths one-off years; a
    company without FCF in all of them gets NaN. Net debt and shares
    come from the latest year, and the price from `market` (one ticker
    per company, see pick_main_ticker). Share counts reported in
    thousands are fixed first (see fix_share_scale).

    The assumptions default to the values in config.py and can be set
    for the whole run (`growth`, `terminal_growth`, `discount_rate`,
    `years`). `growth_by_company` maps a CD_CVM to its own growth rate
    for the first stage, e.g. {24805: 0.10}; the other companies use
    `growth`. The rate used for each company is in GROWTH.

    Returns one row per investable company with a price, sorted by
    UPSIDE = INTRINSIC_VALUE / PRICE - 1 (from the most undervalued).
    """
    growth_by_company = growth_by_company or {}

    latest_year = history_full["YEAR"].max()
    first_year = latest_year - base_years + 1

    recent = history_full[history_full["YEAR"] >= first_year]
    fcf_count = recent.groupby("CD_CVM")["FCF"].count()
    base_fcf = recent.groupby("CD_CVM")["FCF"].mean()
    base_fcf[fcf_count < base_years] = float("nan")
    base_fcf = base_fcf.rename("BASE_FCF").reset_index()

    latest = history_full[(history_full["YEAR"] == latest_year) & history_full["IS_INVESTABLE"]]
    table = latest[["CD_CVM", "DENOM_CIA", "NET_DEBT", "EQUITY", "SHARES"]]
    table = table.merge(base_fcf, on="CD_CVM", how="left")
    table = table.merge(market, on="CD_CVM", how="inner")
    table = fix_share_scale(table)

    table["GROWTH"] = [growth_by_company.get(code, growth) for code in table["CD_CVM"]]
    table["INTRINSIC_VALUE"] = [
        intrinsic_value(fcf, debt, shares, growth=rate, terminal_growth=terminal_growth,
                        discount_rate=discount_rate, years=years)
        for fcf, debt, shares, rate in zip(table["BASE_FCF"], table["NET_DEBT"],
                                           table["SHARES"], table["GROWTH"])
    ]
    table["UPSIDE"] = table["INTRINSIC_VALUE"] / table["PRICE"] - 1
    columns = ["CD_CVM", "DENOM_CIA", "TICKER", "BASE_FCF", "NET_DEBT", "EQUITY", "SHARES",
               "SHARES_FIXED", "PRICE_TO_BOOK", "GROWTH", "INTRINSIC_VALUE", "PRICE", "UPSIDE",
               "AVG_TRADED_VALUE"]
    return table[columns].sort_values("UPSIDE", ascending=False).reset_index(drop=True)


def sensitivity_table(base_fcf, net_debt, shares, discount_rates, growth_rates):
    """Return the intrinsic value per share for a grid of assumptions.

    Rows are discount rates and columns are growth rates (first stage);
    the other assumptions keep their default values. The DCF is very
    sensitive to these two inputs, so a single number is rarely enough.
    """
    table = {}
    for growth in growth_rates:
        table[f"g={growth:.0%}"] = [
            intrinsic_value(base_fcf, net_debt, shares, growth=growth, discount_rate=rate)
            for rate in discount_rates
        ]
    return pd.DataFrame(table, index=[f"r={rate:.0%}" for rate in discount_rates])
