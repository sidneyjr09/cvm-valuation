"""Tests for cvm_valuation.registry."""
import pandas as pd

from cvm_valuation.registry import add_flags, prepare_registry


def make_registry(rows):
    """Build a small registry with the columns used by the pipeline."""
    defaults = {
        "CD_CVM": 111,
        "SETOR_ATIV": "Comércio (Atacado e Varejo)",
        "SIT": "ATIVO",
        "CATEG_REG": "Categoria A",
        "TP_MERC": "BOLSA",
        "SIT_EMISSOR": "FASE OPERACIONAL",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_prepare_registry_keeps_one_row_per_company():
    cad = make_registry([
        {"CD_CVM": 111, "TP_MERC": "BALCÃO ORGANIZADO"},
        {"CD_CVM": 111, "TP_MERC": "BOLSA"},
        {"CD_CVM": 222},
    ])
    registry = prepare_registry(cad)
    assert registry["CD_CVM"].is_unique
    assert len(registry) == 2


def test_prepare_registry_prefers_exchange_row():
    cad = make_registry([
        {"TP_MERC": "BALCÃO ORGANIZADO"},
        {"TP_MERC": "BOLSA"},
        {"TP_MERC": "BALCÃO NÃO ORGANIZADO"},
    ])
    registry = prepare_registry(cad)
    assert registry["TP_MERC"].iloc[0] == "BOLSA"


def test_add_flags_keeps_all_history_rows():
    history = pd.DataFrame({"CD_CVM": [111, 111, 999], "YEAR": [2024, 2025, 2025]})
    registry = prepare_registry(make_registry([{"CD_CVM": 111}]))
    result = add_flags(history, registry)
    assert len(result) == len(history)


def test_add_flags_marks_financial_companies():
    history = pd.DataFrame({"CD_CVM": [111, 222, 333], "YEAR": [2025, 2025, 2025]})
    registry = prepare_registry(make_registry([
        {"CD_CVM": 111, "SETOR_ATIV": "Bancos"},
        {"CD_CVM": 222, "SETOR_ATIV": "Emp. Adm. Part. - Seguradoras e Corretoras"},
        {"CD_CVM": 333},
    ]))
    result = add_flags(history, registry).set_index("CD_CVM")
    assert result.loc[111, "IS_FINANCIAL"]
    assert result.loc[222, "IS_FINANCIAL"]
    assert not result.loc[333, "IS_FINANCIAL"]


def test_add_flags_marks_investable_companies():
    history = pd.DataFrame({"CD_CVM": [1, 2, 3, 4, 5, 6, 7], "YEAR": [2025] * 7})
    registry = prepare_registry(make_registry([
        {"CD_CVM": 1},                                    # investable
        {"CD_CVM": 2, "SIT": "CANCELADA"},                # inactive
        {"CD_CVM": 3, "CATEG_REG": "Categoria B"},        # no traded shares
        {"CD_CVM": 4, "TP_MERC": "BALCÃO ORGANIZADO"},    # not on the exchange
        {"CD_CVM": 5, "SIT_EMISSOR": "EM RECUPERAÇÃO JUDICIAL OU EQUIVALENTE"},
        {"CD_CVM": 6, "SETOR_ATIV": "Bancos"},            # financial
    ]))
    result = add_flags(history, registry).set_index("CD_CVM")
    assert result.loc[1, "IS_INVESTABLE"]
    for code in [2, 3, 4, 5, 6]:
        assert not result.loc[code, "IS_INVESTABLE"], f"Company {code} should not be investable"
    # Company 7 is missing from the registry: kept in the history, not investable
    assert not result.loc[7, "IS_INVESTABLE"]
