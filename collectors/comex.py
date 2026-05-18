"""
Cobre & Alumínio COMEX — preços históricos via Stooq (CSV).
Converte USD/lb → USD/ton métrica para comparação com LME.
"""

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

TICKERS = {
    "COMEX_Copper":   {"symbol": "hg.f",  "unit": "USD/lb",  "exchange": "COMEX"},
    "COMEX_Aluminum": {"symbol": "ali.f", "unit": "USD/lb",  "exchange": "COMEX"},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "COMEX_metals.xlsx"
LB_TO_MT = 2204.62  # 1 metric ton = 2204.62 lb


def fetch_stooq(symbol: str) -> pd.DataFrame | None:
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"    erro HTTP: {e}")
        return None

    text = r.text.strip()
    if not text or text.lower().startswith("no data"):
        print("    Stooq retornou vazio")
        return None

    try:
        df = pd.read_csv(StringIO(text))
    except Exception as e:
        print(f"    erro parse: {e}")
        return None

    if df.empty:
        return None

    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results = {}

    for name, meta in TICKERS.items():
        print(f"\n=== {name} ({meta['symbol']}) — {meta['exchange']}, {meta['unit']} ===")
        df = fetch_stooq(meta["symbol"])

        if df is None or df.empty:
            print("  Sem dados.")
            continue

        results[name] = df
        print(f"  Período: {df.index.min().date()} -> {df.index.max().date()}  ({len(df)} pregões)")
        print(f"  Último close: {df['close'].iloc[-1]:.4f} {meta['unit']}")

    combined = pd.DataFrame({
        name: df["close"] for name, df in results.items()
    }).sort_index()

    if "COMEX_Copper" in combined.columns:
        combined["COMEX_Copper_USDperMT"] = combined["COMEX_Copper"] * LB_TO_MT
    if "COMEX_Aluminum" in combined.columns:
        combined["COMEX_Aluminum_USDperMT"] = combined["COMEX_Aluminum"] * LB_TO_MT

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in results.items():
            df.to_excel(writer, sheet_name=name[:31])
        combined.to_excel(writer, sheet_name="Combined")

    print(f"Pronto: {OUTPUT_FILE}")
    print(f"\nÚltimos 5 dias (close):")
    print(combined.tail().to_string())


if __name__ == "__main__":
    main()
