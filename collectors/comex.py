"""
Cobre & Alumínio — preços spot mensais via Alpha Vantage.
Requer: ALPHA_VANTAGE_API_KEY no .env  (chave gratuita: alphavantage.co)
Frequência: mensal (Alpha Vantage não oferece diário para commodities físicas).
Ambas as séries retornam em USD/ton métrica.
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "metals_spot.xlsx"

COMMODITIES = {
    "Copper":   {"function": "COPPER"},
    "Aluminum": {"function": "ALUMINUM"},
}


def fetch_av_commodity(function: str, api_key: str) -> tuple[pd.DataFrame | None, str]:
    """Retorna (DataFrame, unit_string). Frequência: mensal."""
    url = "https://www.alphavantage.co/query"
    params = {"function": function, "interval": "monthly", "apikey": api_key}

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print(f"  erro HTTP: {e}")
        return None, ""

    if "data" not in j:
        msg = j.get("Information") or j.get("Note") or str(list(j.keys()))
        print(f"  FAIL: {msg}")
        return None, ""

    unit = j.get("unit", "USD/MT")
    df = pd.DataFrame(j["data"])
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date").sort_index().dropna()
    return df, unit


def main():
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("ERRO: ALPHA_VANTAGE_API_KEY não configurada no .env")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results = {}

    for name, meta in COMMODITIES.items():
        print(f"\n=== {name} (Alpha Vantage: {meta['function']}) ===")
        df, unit = fetch_av_commodity(meta["function"], api_key)
        time.sleep(1.2)  # free tier: max 1 req/seg

        if df is None or df.empty:
            print("  Sem dados.")
            continue

        results[name] = df
        print(f"  Período: {df.index.min().date()} -> {df.index.max().date()}  ({len(df)} meses)")
        print(f"  Último: {df['value'].iloc[-1]:,.2f} {unit}")

    if not results:
        print("Nenhum dado coletado.")
        return

    combined = pd.DataFrame({name: df["value"] for name, df in results.items()})

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in results.items():
            df.to_excel(writer, sheet_name=name)
        combined.to_excel(writer, sheet_name="Combined")

    print("Pronto.")


if __name__ == "__main__":
    main()
