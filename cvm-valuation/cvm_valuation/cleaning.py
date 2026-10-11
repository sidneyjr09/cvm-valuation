def split_by_company(df):
    """Clean a CVM statement and split it by company.

    Keeps only the most recent document of each company
    (latest DT_REFER, then latest VERSAO), drops duplicated rows and
    converts values to thousands of reais. Returns a dictionary
    mapping each CD_CVM to its DataFrame.
    """
    df_clean = df[(df["ORDEM_EXERC"] == "ÚLTIMO") & (~df.duplicated())]
    is_unit = df_clean["ESCALA_MOEDA"] == "UNIDADE"
    df_clean.loc[is_unit, "VL_CONTA"] /= 1000
    df_clean.loc[is_unit, "ESCALA_MOEDA"] = "MIL"
    companies_data = {}
    for code, group in df_clean.groupby("CD_CVM"):
        latest_date = group["DT_REFER"].max()
        group = group[group["DT_REFER"] == latest_date]
        latest_version = group["VERSAO"].max()
        group = group[group["VERSAO"] == latest_version]
        companies_data[code] = group
    return companies_data