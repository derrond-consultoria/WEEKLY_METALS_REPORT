"""
Westmetall LME scraper — Cobre & Alumínio
Baixa Cash, 3M e Stock desde 2010 até o ano atual.
Exporta num único XLSX com 3 abas: Copper, Aluminium, Combined.
"""

import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

FIELDS = {
    "Copper":    "LME_Cu_cash",
    "Aluminium": "LME_Al_cash",
}

START_YEAR  = 2010
END_YEAR    = datetime.now().year
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "LME_Westmetall.xlsx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

DATE_RE = r"^\d{1,2}\.\s+[A-Za-z]+\s+\d{4}$"


def fetch_year(field: str, year: int) -> pd.DataFrame | None:
    url = (
        f"https://www.westmetall.com/en/markdaten.php"
        f"?action=table&field={field}&year={year}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        dfs = pd.read_html(StringIO(r.text), decimal=".", thousands=",")
    except Exception as e:
        print(f"    erro: {e}")
        return None

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    if df.shape[1] < 4:
        return None

    df = df.iloc[:, :4]
    df.columns = ["Date", "Cash", "3M", "Stock"]

    mask = df["Date"].astype(str).str.match(DATE_RE)
    df = df[mask].copy()
    if df.empty:
        return None

    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])

    for col in ["Cash", "3M", "Stock"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["Cash", "3M", "Stock"], how="all")


def fetch_metal(name: str, field: str) -> pd.DataFrame:
    frames = []
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"  {name} {year}...", end=" ", flush=True)
        df = fetch_year(field, year)
        if df is not None and not df.empty:
            frames.append(df)
            print(f"OK ({len(df)} linhas)")
        else:
            print("vazio")
        time.sleep(0.4)

    if not frames:
        return pd.DataFrame(columns=["Cash", "3M", "Stock"])

    return (
        pd.concat(frames, ignore_index=True)
          .drop_duplicates(subset=["Date"])
          .sort_values("Date")
          .set_index("Date")
    )


SHEET_NAMES = {"Copper": "Preco_LME_Cu", "Aluminium": "Preco_LME_Al"}


def collect() -> dict[str, pd.DataFrame]:
    data = {}
    for metal_name, field in FIELDS.items():
        print(f"\n=== LME {metal_name} ===")
        df = fetch_metal(metal_name, field)
        if not df.empty:
            print(f"  {df.index.min().date()} -> {df.index.max().date()}  ({len(df)} linhas)")
            data[SHEET_NAMES[metal_name]] = df
    return data


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sheets = collect()

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name)
    print(f"Pronto: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
