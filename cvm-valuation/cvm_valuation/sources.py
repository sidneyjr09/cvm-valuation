import io
import zipfile
from datetime import date
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import DATA_DIR

def find_zips(url):
    """Return a dictionary mapping each year to its zip URL."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    tags = soup.find_all("a")
    zip_dict = {}
    for tag in tags:
        href = tag.get("href")
        if not href:
            continue
        if href.endswith(".zip"):
            year = int(href.removesuffix(".zip")[-4:])
            link = urljoin(url, href)
            zip_dict[year] = link
    return zip_dict

def complete_years(zip_links):
    """Return only the years whose DFP files are complete.

    Excludes the current year and, before April, also the previous
    year, since companies have until the end of March to file.
    """
    today = date.today()
    complete_year_links = {}
    for year, link in zip_links.items():
        if (year == today.year - 1 and today.month < 4) or (year >= today.year):
            continue
        complete_year_links[year] = link
    return complete_year_links

def get_file(link, use_cache=True):
    """Return a file from the given URL as an in-memory buffer.

    By default, the file is cached in DATA_DIR and only downloaded if it
    is not there yet. With use_cache=False, it is always downloaded and
    never saved.
    """
    if not use_cache:
        response = requests.get(link, timeout=60)
        response.raise_for_status()
        return io.BytesIO(response.content)
    DATA_DIR.mkdir(exist_ok=True)
    file_name = link.split("/")[-1]
    file_path = DATA_DIR / file_name
    if not file_path.exists():
        response = requests.get(link, timeout=60)
        response.raise_for_status()
        file_path.write_bytes(response.content)
    return io.BytesIO(file_path.read_bytes())

def open_csv(zip_file, statement, basis, year, doc_type="dfp"):
    """Read a statement CSV from a CVM zip (DFP or ITR) and return a DataFrame."""
    with zipfile.ZipFile(zip_file) as z:
        if basis is None:
            csv_name = f"{doc_type}_cia_aberta_{statement}_{year}.csv"
        else:
            csv_name = f"{doc_type}_cia_aberta_{statement}_{basis}_{year}.csv"
        df = pd.read_csv(z.open(csv_name), sep=";", encoding="latin-1")
    return df