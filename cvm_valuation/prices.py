import pandas as pd
import yfinance as yf

from .config import PRICE_PERIOD


def fetch_market_data(tickers, period=PRICE_PERIOD):
    """Return the latest price and the liquidity of each ticker.

    Downloads daily prices from Yahoo Finance, where B3 tickers end in
    ".SA". PRICE is the last closing price, not adjusted for dividends,
    so it is comparable with a value per share computed from today's
    share count. AVG_TRADED_VALUE is the average daily traded value
    (close x volume) over the period, in reais. Tickers without data
    get NaN.
    """
    symbols = [f"{ticker}.SA" for ticker in tickers]
    data = yf.download(symbols, period=period, auto_adjust=False,
                       progress=False, multi_level_index=True)
    close = data["Close"]
    volume = data["Volume"]
    rows = []
    for ticker, symbol in zip(tickers, symbols):
        if symbol in close.columns:
            prices = close[symbol].dropna()
            price = prices.iloc[-1] if len(prices) > 0 else float("nan")
            traded_value = (close[symbol] * volume[symbol]).mean()
        else:
            price = float("nan")
            traded_value = float("nan")
        rows.append({"TICKER": ticker, "PRICE": price, "AVG_TRADED_VALUE": traded_value})
    return pd.DataFrame(rows)


def pick_main_ticker(tickers, market):
    """Keep one ticker per company: the most traded one with a price.

    The most liquid class is not always the common share (Petrobras
    trades mostly PETR4), so the choice is based on the average daily
    traded value. Returns the columns CD_CVM, TICKER, PRICE and
    AVG_TRADED_VALUE.
    """
    table = tickers.merge(market, on="TICKER", how="inner")
    table = table[table["PRICE"].notna()]
    table = table.sort_values("AVG_TRADED_VALUE", ascending=False)
    table = table.drop_duplicates(subset="CD_CVM", keep="first")
    return table[["CD_CVM", "TICKER", "PRICE", "AVG_TRADED_VALUE"]].reset_index(drop=True)
