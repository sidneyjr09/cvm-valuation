import pandas as pd

from .config import SHARE_TYPES, TICKER_PATTERN
from .sources import company_ids, get_file, open_csv


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


def build_tickers(fca_links, dfp_links):
    """Return the current tickers of each company, with its CVM code.

    Takes the FCA and DFP dictionaries mapping each year to its zip URL
    and uses the latest year of each. The FCA describes the company
    today, so its latest zip is used even if the year is not over. The
    FCA identifies companies only by CNPJ, so the CVM code is taken from
    the balance sheet (BPP) of the latest DFP. Returns one row per
    ticker, with the columns CD_CVM, TICKER and SHARE_TYPE.
    """
    fca_year = max(fca_links)
    dfp_year = max(dfp_links)
    securities = open_csv(get_file(fca_links[fca_year]), "valor_mobiliario", None, fca_year, "fca")
    tickers = prepare_tickers(securities)
    ids = company_ids(get_file(dfp_links[dfp_year]), dfp_year)
    tickers = tickers.merge(ids, on="CNPJ_CIA", how="inner")
    tickers = tickers.rename(columns={"Valor_Mobiliario": "SHARE_TYPE"})
    return tickers[["CD_CVM", "TICKER", "SHARE_TYPE"]].reset_index(drop=True)
