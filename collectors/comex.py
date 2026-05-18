"""
Cobre & Alumínio COMEX — contratos contínuos via Nasdaq Data Link (CHRIS/CME).
Requer: NASDAQ_API_KEY no .env
Preços: Settle em USD/lb → convertido para USD/ton métrica.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "COMEX_metals.xlsx"
LB_TO_MT = 2204.62

DATASETS = {
    "COMEX_Copper":   "CHRIS/CME_HG1",   # High Grade Copper, USD/lb
    "COMEX_Aluminum": "CHRIS/CME_ALI1",  # Aluminum MW US (desde 2019), USD/lb
}


def fetch_chris(dataset: str, api_key: str, start: str = "2010-01-01") -> pd.DataFrame | None:
    """Baixa série histórica de um dataset CHRIS via Nasdaq Data Link."""
    url = f"https://data.nasdaq.com/api/v3/datasets/{dataset}.json"
    params = {"api_key": api_key, "start_date": start, "order": "asc"}

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()["dataset"]
    except Exception as e:
        print(f"  erro ({dataset}): {e}")
        return None

    if not j.get("data"):
        print(f"  sem dados para {dataset}")
        return None

    cols = [c.lower().replace(" ", "_") for c in j["column_names"]]
    df = pd.DataFrame(j["data"], columns=cols)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def main():
    api_key = os.getenv("NASDAQ_API_KEY")
    if not api_key:
        print("ERRO: NASDAQ_API_KEY não configurada no .env")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results = {}

    for name, dataset in DATASETS.items():
        print(f"\n=== {name} ({dataset}) ===")
        df = fetch_chris(dataset, api_key)
        if df is None:
            continue

        results[name] = df
        last_settle = df["settle"].iloc[-1]
        print(f"  Período: {df.index.min().date()} -> {df.index.max().date()}  ({len(df)} pregões)")
        print(f"  Último settle: {last_settle:.4f} USD/lb  =  {last_settle * LB_TO_MT:,.0f} USD/MT")

    if not results:
        print("Nenhum dado coletado.")
        return

    combined = pd.DataFrame({name: df["settle"] for name, df in results.items()})
    for name in list(results):
        combined[f"{name}_USDperMT"] = combined[name] * LB_TO_MT

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in results.items():
            df.to_excel(writer, sheet_name=name[:31])
        combined.to_excel(writer, sheet_name="Combined")

    print("Pronto.")


if __name__ == "__main__":
    main()
