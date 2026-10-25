import pandas as pd

from .sources import company_ids, get_file, open_csv

def prepare_shares(shares):
    """Return the shares outstanding of each company in one year.

    Keeps the latest document of each company (latest DT_REFER, then
    latest VERSAO) and subtracts treasury shares from the total issued.
    Returns the columns CNPJ_CIA and SHARES, in number of shares.
    """
    latest = shares.sort_values(["CNPJ_CIA", "DT_REFER", "VERSAO"])
    latest = latest.drop_duplicates(subset="CNPJ_CIA", keep="last")
    latest["SHARES"] = latest["QT_ACAO_TOTAL_CAP_INTEGR"] - latest["QT_ACAO_TOTAL_TESOURO"]
    return latest[["CNPJ_CIA", "SHARES"]]

def build_shares_history(dfp_links):
    """Build the shares outstanding history of all companies.

    Takes a dictionary mapping each year to its DFP zip URL and returns
    a single DataFrame with one row per company and year, with the
    columns CD_CVM, YEAR and SHARES (in number of shares, not thousands).

    The share capital file identifies companies only by CNPJ, so the
    CVM code is taken from the balance sheet (BPP) of the same zip.
    Companies missing from either file are dropped.
    """
    tables = []
    for year, link in dfp_links.items():
        print(f"Processing {year}...")
        zip_data = get_file(link)
        try:
            raw_shares = open_csv(zip_data, "composicao_capital", None, year, "dfp")
        except KeyError:
            print(f"No share capital file for {year}, skipping")
            continue
        shares_data = prepare_shares(raw_shares)
        ids = company_ids(zip_data, year)
        shares_table = shares_data.merge(ids, on="CNPJ_CIA", how="inner")
        shares_table["YEAR"] = year
        shares_table = shares_table[["CD_CVM", "YEAR", "SHARES"]]
        tables.append(shares_table)
    return pd.concat(tables, ignore_index=True)

