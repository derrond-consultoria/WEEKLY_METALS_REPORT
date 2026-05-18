"""
Brent Crude e PVC DCE — preços históricos.
  Brent: EIA API (Europe Brent Spot Price FOB, USD/barril) — requer EIA_API_KEY
  PVC:   DCE contrato principal contínuo (V0) via akshare, CNY/ton
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "energy_pvc.xlsx"
EIA_SERIES_BRENT = "RBRTE"  # Europe Brent Spot Price FOB


def fetch_brent_eia(api_key: str, start: str = "2010-01-01") -> pd.DataFrame | None:
    """
    Brent Spot Price via EIA API v2.
    Chave gratuita em: https://www.eia.gov/opendata/register.php
    """
    url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
    params = {
        "api_key":              api_key,
        "frequency":            "daily",
        "data[0]":              "value",
        "facets[series][]":     EIA_SERIES_BRENT,
        "start":                start,
        "sort[0][column]":      "period",
        "sort[0][direction]":   "asc",
        "length":               5000,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print(f"  erro EIA: {e}")
        return None

    rows = j.get("response", {}).get("data", [])
    if not rows:
        print("  EIA: sem dados retornados")
        return None

    df = pd.DataFrame(rows)[["period", "value"]]
    df.columns = ["date", "close"]
    df["date"]  = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.set_index("date").sort_index().dropna()


def fetch_pvc_dce() -> pd.DataFrame | None:
    """PVC DCE contrato principal contínuo (V0) via akshare, CNY/ton."""
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
        "日期": "date", "开盘价": "open", "最高价": "high",
        "最低价": "low", "收盘价": "close", "成交量": "volume",
        "持仓量": "open_interest", "动态结算价": "settlement",
    })
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    for col in df.select_dtypes(exclude="number").columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results = {}

    print("=== Brent Crude (EIA) ===")
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        print("  AVISO: EIA_API_KEY não configurada — Brent ignorado")
    else:
        df_brent = fetch_brent_eia(api_key)
        if df_brent is not None:
            results["Brent"] = df_brent
            print(f"  {df_brent.index.min().date()} -> {df_brent.index.max().date()}  "
                  f"último: {df_brent['close'].iloc[-1]:.2f} USD/bbl")

    print("\n=== PVC DCE (V0) ===")
    df_pvc = fetch_pvc_dce()
    if df_pvc is not None:
        results["PVC_DCE"] = df_pvc
        print(f"  {df_pvc.index.min().date()} -> {df_pvc.index.max().date()}  "
              f"último: {df_pvc['close'].iloc[-1]:.0f} CNY/ton")

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
