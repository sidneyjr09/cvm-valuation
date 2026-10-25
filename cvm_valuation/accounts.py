def find_account(company, code):
    """Return the value of one account of a company.

    Returns NaN if the account is missing and raises ValueError if it
    appears more than once.
    """
    is_account = company["CD_CONTA"] == code
    rows = company[is_account]
    values = rows["VL_CONTA"]
    if len(values) == 0:
        return float("nan")
    elif len(values) == 1:
        return values.iloc[0]
    else:
        company_code = company["CD_CVM"].iloc[0]
        raise ValueError(f"Company {company_code} has {len(values)} rows for account {code}")