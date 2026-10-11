from .config import FINANCIAL_KEYWORDS

def prepare_registry(cad):
    """Keep one row per company with the columns used in the analysis."""
    registry = cad[["CD_CVM", "SETOR_ATIV", "SIT", "CATEG_REG", "TP_MERC", "SIT_EMISSOR"]]
    registry = registry.sort_values("TP_MERC", ascending=False)
    registry = registry.drop_duplicates(subset="CD_CVM")
    return registry

def add_flags(history, registry):
    """Merge the registry into the history and add the IS_FINANCIAL and IS_INVESTABLE flags."""
    history_full = history.merge(registry, on="CD_CVM", how="left")
    history_full["IS_FINANCIAL"] = history_full["SETOR_ATIV"].str.contains(FINANCIAL_KEYWORDS, na=False)

    is_active = history_full["SIT"] == "ATIVO"
    is_category_a = history_full["CATEG_REG"] == "Categoria A"
    is_listed = history_full["TP_MERC"] == "BOLSA"
    is_operating = history_full["SIT_EMISSOR"] == "FASE OPERACIONAL"
    is_not_financial = ~history_full["IS_FINANCIAL"]

    history_full["IS_INVESTABLE"] = (
        is_active & is_category_a & is_listed & is_operating & is_not_financial
    )
    return history_full