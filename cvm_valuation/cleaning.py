import pandas as pd


def split_by_company(df):
    """Clean a CVM statement and split it by company.

    Keeps only the most recent document of each company
    (latest DT_REFER, then latest VERSAO), drops duplicated rows and
    converts values to thousands of reais. In statements of a period
    (with DT_INI_EXERC), an account reported for two start dates in the
    same document keeps the longest period. Returns a dictionary
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
        if "DT_INI_EXERC" in group.columns:
            group = group.sort_values("DT_INI_EXERC").drop_duplicates(subset="CD_CONTA", keep="first")
        companies_data[code] = group
    return companies_data


def pick_statement(consolidated, individual):
    """Return one version of a statement per company.

    Companies with subsidiaries publish consolidated statements; the
    others publish only the individual ones, and some (TIM since 2024)
    fill the consolidated form with zeros. For each company, the
    consolidated rows are kept when they hold any value; otherwise its
    individual rows are used.
    """
    latest = consolidated[consolidated["ORDEM_EXERC"] == "ÚLTIMO"]
    has_values = (latest["VL_CONTA"] != 0).groupby(latest["CD_CVM"]).any()
    with_values = has_values[has_values].index
    use_consolidated = consolidated[consolidated["CD_CVM"].isin(with_values)]
    use_individual = individual[~individual["CD_CVM"].isin(with_values)]
    return pd.concat([use_consolidated, use_individual], ignore_index=True)

