import pandas as pd

from .config import SHARE_TYPES, TICKER_PATTERN


def prepare_tickers(securities):
    """Return the stock tickers still traded on the exchange.

    Keeps common and preferred shares listed on the exchange (B3), with
    no end-of-trading date and a valid ticker (four characters plus one
    or two digits). Units are left out, since each unit bundles several
    shares. Returns one row per ticker, with the columns CNPJ_CIA,
    TICKER and Valor_Mobiliario.
    """
    is_share = securities["Valor_Mobiliario"].isin(SHARE_TYPES)
    is_listed = securities["Mercado"] == "Bolsa"
    is_traded = securities["Data_Fim_Negociacao"].isna()
    is_valid = securities["Codigo_Negociacao"].str.fullmatch(TICKER_PATTERN, na=False)
    tickers = securities[is_share & is_listed & is_traded & is_valid]
    tickers = tickers.drop_duplicates(subset=["CNPJ_Companhia", "Codigo_Negociacao"])
    tickers = tickers.rename(columns={"CNPJ_Companhia": "CNPJ_CIA", "Codigo_Negociacao": "TICKER"})
    return tickers[["CNPJ_CIA", "TICKER", "Valor_Mobiliario"]]