"""Shared helpers for the tests.

pytest loads this file automatically before running the tests. The
fixture below can be used by any test function that lists
`make_statement` as a parameter.
"""
import pandas as pd
import pytest


@pytest.fixture
def make_statement():
    """Return a function that builds a small CVM-like statement.

    Each row is a dictionary; columns that are not given get typical
    default values, so each test only lists the columns it cares about.
    """
    defaults = {
        "CD_CVM": 111,
        "DENOM_CIA": "ALFA S.A.",
        "DT_REFER": "2025-12-31",
        "VERSAO": 1,
        "ESCALA_MOEDA": "MIL",
        "ORDEM_EXERC": "ÚLTIMO",
        "CD_CONTA": "6.01",
        "DS_CONTA": "Caixa Líquido Atividades Operacionais",
        "VL_CONTA": 0.0,
    }

    def _make(rows):
        return pd.DataFrame([{**defaults, **row} for row in rows])

    return _make
