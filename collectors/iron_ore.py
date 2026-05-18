"""
Minério de Ferro 62% Fe CFR China — preços históricos.
Fonte: DCE contrato principal contínuo (I0) via akshare, cotado em CNY/ton.
O contrato DCE de minério de ferro rastreia o índice 62% Fe CFR Qingdao.
"""

import sys
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "iron_ore.csv"
START_DATE  = "20130501"  # DCE iron ore futures iniciaram em maio/2013


def fetch_iron_ore(start_date: str = START_DATE, end_date: str | None = None) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.today().strftime("%Y%m%d")

    print(f"Baixando minério de ferro DCE (I0) de {start_date} a {end_date}...")
    df = ak.futures_main_sina(symbol="I0", start_date=start_date, end_date=end_date)

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


def collect() -> dict[str, pd.DataFrame]:
    print("\n=== Minério de Ferro 62% Fe (I0) ===")
    df = fetch_iron_ore()
    print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
          f"último: {df['close'].iloc[-1]:.0f} CNY/ton")
    return {"Preco_Minerio_Fe": df}


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sheets = collect()
    sheets["Preco_Minerio_Fe"].to_csv(OUTPUT_FILE, encoding="utf-8-sig")
    print(f"\nSalvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
