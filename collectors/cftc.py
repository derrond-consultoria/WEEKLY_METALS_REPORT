"""
CFTC Managed Money — posições long/short de gestores de recursos.
Fonte: Nasdaq Data Link (QDL/FON).
Requer: NASDAQ_API_KEY no .env
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "cftc"

CODES = {
    "COPPER":      "085692",
    "ALUMINIUM":   "191691",
    "BRENT": "06765T",
}


def get_cftc_mm(api_key: str, code: str, name: str) -> pd.Series:
    """Retorna série semanal Managed Money Net para um contrato CFTC."""
    params = {
        "contract_code": code,
        "type": "F_ALL",
        "qopts.columns": "date,money_manager_longs,money_manager_shorts",
        "api_key": api_key,
    }
    r = requests.get(
        "https://data.nasdaq.com/api/v3/datatables/QDL/FON",
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    j = r.json()["datatable"]

    if not j["data"]:
        raise ValueError(f"Sem dados para contract_code={code}")

    cols = [c["name"] for c in j["columns"]]
    df = pd.DataFrame(j["data"], columns=cols)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df["money_manager_longs"]  = pd.to_numeric(df["money_manager_longs"],  errors="coerce")
    df["money_manager_shorts"] = pd.to_numeric(df["money_manager_shorts"], errors="coerce")
    df["mm_net"] = df["money_manager_longs"] - df["money_manager_shorts"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / f"managed_money_{name}.csv")

    s = df["mm_net"]
    s.name = name
    return s


def main():
    api_key = os.getenv("NASDAQ_API_KEY")
    if not api_key:
        print("ERRO: NASDAQ_API_KEY não configurada no .env")
        sys.exit(1)

    for name, code in CODES.items():
        print(f"{name}...", end=" ", flush=True)
        try:
            s = get_cftc_mm(api_key, code, name)
            print(f"OK — último: {s.index[-1].date()}  net={s.iloc[-1]:,.0f}")
        except Exception as e:
            print(f"ERRO: {e}")


if __name__ == "__main__":
    main()
