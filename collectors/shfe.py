"""
SHFE Hot Rolled Coil (HC) — preços históricos via akshare.
Contrato principal contínuo HC0, cotado em CNY/ton.
"""

import sys
from pathlib import Path

import akshare as ak
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "SHFE_HRC.csv"
START_DATE  = "20140301"  # HRC começou a ser negociado na SHFE em 21/03/2014


def fetch_hrc_main(start_date: str = START_DATE, end_date: str | None = None) -> pd.DataFrame:
    from datetime import datetime
    if end_date is None:
        end_date = datetime.today().strftime("%Y%m%d")

    print(f"Baixando HC0 (contrato principal) de {start_date} a {end_date}...")
    df = ak.futures_main_sina(symbol="HC0", start_date=start_date, end_date=end_date)

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

    for col in ["open", "high", "low", "close", "volume", "open_interest", "settlement"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def collect() -> dict[str, pd.DataFrame]:
    print("\n=== SHFE HRC (HC0) ===")
    df = fetch_hrc_main()
    print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
          f"último close: {df['close'].iloc[-1]:.0f} CNY/ton")
    return {"Preco_SHFE_HRC": df}


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sheets = collect()
    df = sheets["Preco_SHFE_HRC"]
    df.to_csv(OUTPUT_FILE, encoding="utf-8-sig")
    print(f"\nSalvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
