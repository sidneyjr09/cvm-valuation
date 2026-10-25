"""Tests for cvm_valuation.sources.

These tests never access the internet: open_csv reads a zip built in
memory, and get_file reads a file that is already in a temporary cache.
"""
import io
import zipfile
from datetime import date

from cvm_valuation.sources import complete_years, get_file, open_csv


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
