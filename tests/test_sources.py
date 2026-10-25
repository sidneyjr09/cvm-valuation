"""Tests for cvm_valuation.sources.

These tests never access the internet: open_csv reads a zip built in
memory, and get_file reads a file that is already in a temporary cache.
"""
import io
import zipfile
from datetime import date

from cvm_valuation.sources import company_ids, complete_years, get_file, open_csv, open_statement


def test_complete_years_excludes_current_year():
    this_year = date.today().year
    links = {this_year: "a", this_year - 1: "b", this_year - 2: "c"}
    kept = complete_years(links)
    assert this_year not in kept
    assert this_year - 2 in kept


def test_complete_years_previous_year_only_from_april():
    this_year = date.today().year
    kept = complete_years({this_year - 1: "b"})
    assert (this_year - 1 in kept) == (date.today().month >= 4)


def test_open_csv_reads_statement_from_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        content = "CD_CVM;VL_CONTA\n111;100.0\n".encode("latin-1")
        z.writestr("dfp_cia_aberta_DFC_MI_con_2025.csv", content)
    buffer.seek(0)
    df = open_csv(buffer, "DFC_MI", "con", 2025)
    assert df["VL_CONTA"].iloc[0] == 100.0


def test_get_file_reads_from_cache(tmp_path, monkeypatch):
    # Point DATA_DIR to a temporary folder, so the real cache is not touched
    monkeypatch.setattr("cvm_valuation.sources.DATA_DIR", tmp_path)
    (tmp_path / "file.zip").write_bytes(b"cached content")
    buffer = get_file("https://example.com/some/path/file.zip")
    assert buffer.read() == b"cached content"


def make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, df in files.items():
            z.writestr(name, df.to_csv(sep=";", index=False).encode("latin-1"))
    buffer.seek(0)
    return buffer


def test_open_statement_combines_consolidated_and_individual(make_statement):
    consolidated = make_statement([
        {"CD_CVM": 111, "VL_CONTA": 100.0},
        {"CD_CVM": 222, "VL_CONTA": 0.0},
    ])
    individual = make_statement([
        {"CD_CVM": 111, "VL_CONTA": 90.0},
        {"CD_CVM": 222, "VL_CONTA": 70.0},
        {"CD_CVM": 333, "VL_CONTA": 30.0},
    ])
    zip_file = make_zip({
        "dfp_cia_aberta_DFC_MI_con_2025.csv": consolidated,
        "dfp_cia_aberta_DFC_MI_ind_2025.csv": individual,
    })
    result = open_statement(zip_file, "DFC_MI", 2025)
    assert sorted(zip(result["CD_CVM"], result["VL_CONTA"])) == [(111, 100.0), (222, 70.0), (333, 30.0)]


def test_open_statement_without_individual_file(make_statement):
    zip_file = make_zip({"dfp_cia_aberta_DFC_MI_con_2025.csv": make_statement([{"VL_CONTA": 100.0}])})
    result = open_statement(zip_file, "DFC_MI", 2025)
    assert list(result["VL_CONTA"]) == [100.0]


def test_company_ids_includes_companies_with_only_individual(make_statement):
    consolidated = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.02.01"},
    ])
    individual = make_statement([
        {"CNPJ_CIA": "11.111.111/0001-11", "CD_CVM": 111, "CD_CONTA": "2.01.04"},
        {"CNPJ_CIA": "22.222.222/0001-22", "CD_CVM": 222, "CD_CONTA": "2.01.04"},
    ])
    zip_file = make_zip({
        "dfp_cia_aberta_BPP_con_2025.csv": consolidated,
        "dfp_cia_aberta_BPP_ind_2025.csv": individual,
    })
    ids = company_ids(zip_file, 2025)
    assert list(ids.columns) == ["CNPJ_CIA", "CD_CVM"]
    assert sorted(ids["CD_CVM"]) == [111, 222]

