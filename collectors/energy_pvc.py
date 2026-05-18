"""
Brent Crude (ICE) e PVC DCE — preços históricos.
- Brent: Stooq (lco.f) → USD/barril
- PVC:   akshare SHFE/DCE contrato principal (V0) → CNY/ton
"""

import sys
from io import StringIO
from pathlib import Path

import akshare as ak
import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "energy_pvc.xlsx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch_brent() -> pd.DataFrame | None:
    """Brent Crude histórico via Stooq (ICE futures, USD/barril)."""
    url = "https://stooq.com/q/d/l/?s=lco.f&i=d"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  erro Brent: {e}")
        return None

    text = r.text.strip()
    if not text or text.lower().startswith("no data"):
        print("  Stooq não retornou dados para Brent")
        return None

    df = pd.read_csv(StringIO(text))
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def fetch_pvc_dce() -> pd.DataFrame | None:
    """PVC DCE contrato principal contínuo (V0) via akshare, CNY/ton."""
    from datetime import datetime
    try:
        df = ak.futures_main_sina(
            symbol="V0",
            start_date="20090101",
            end_date=datetime.today().strftime("%Y%m%d"),
        )
    except Exception as e:
        print(f"  erro PVC akshare: {e}")
        return None

    df = df.rename(columns={
        "日期": "date",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "成交量": "volume",
        "持仓量": "open_interest",
        "动态结算价": "settlement",
    })
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    for col in df.select_dtypes(exclude="number").columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results = {}

    print("=== Brent Crude (ICE) ===")
    df_brent = fetch_brent()
    if df_brent is not None:
        results["Brent"] = df_brent
        print(f"  {df_brent.index.min().date()} -> {df_brent.index.max().date()}  "
              f"último close: {df_brent['close'].iloc[-1]:.2f} USD/bbl")

    print("\n=== PVC DCE (V0) ===")
    df_pvc = fetch_pvc_dce()
    if df_pvc is not None:
        results["PVC_DCE"] = df_pvc
        print(f"  {df_pvc.index.min().date()} -> {df_pvc.index.max().date()}  "
              f"último close: {df_pvc['close'].iloc[-1]:.0f} CNY/ton")

    if not results:
        print("Nenhum dado coletado.")
        return

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in results.items():
            df.to_excel(writer, sheet_name=name)

    print("Pronto.")


if __name__ == "__main__":
    main()
