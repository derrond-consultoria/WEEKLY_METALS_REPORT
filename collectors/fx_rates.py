"""
Câmbio e Juros — séries históricas diárias.

Fontes:
  USD/BRL PTAX  → API Banco Central do Brasil (gratuita, sem chave)
  EUR/USD        → ECB Statistical Data Warehouse (gratuita, sem chave)
  CNY/USD        → FRED `DEXCHUS`  (CNY por 1 USD)
  DXY            → FRED `DTWEXBGS` (Nominal Broad USD Index — proxy do DXY ICE)
  US Treasury 10Y→ FRED `DGS10`
  DI Fut Jan/XX  → TODO: B3/ANBIMA (sem API pública estável disponível)

FRED requer chave gratuita: https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "fx_rates.xlsx"

FRED_SERIES = {
    "CNY_USD": "DEXCHUS",    # Chinese Yuan per 1 USD (quanto CNY vale 1 USD)
    "DXY":     "DTWEXBGS",   # Nominal Broad U.S. Dollar Index (Fed) ≈ DXY ICE
    "US10Y":   "DGS10",      # 10-Year Treasury Constant Maturity Rate (% a.a.)
}


# ── PTAX (Banco Central do Brasil) ────────────────────────────────────────────

def fetch_ptax(start: str = "01-01-2010") -> pd.DataFrame | None:
    end = datetime.today().strftime("%m-%d-%Y")
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarPeriodo(dataInicial=@di,dataFinalCotacao=@df)"
        f"?@di='{start}'&@df='{end}'&$format=json"
        "&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao"
    )
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json().get("value", [])
    except Exception as e:
        print(f"  erro PTAX: {e}")
        return None

    if not data:
        return None

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["dataHoraCotacao"]).dt.normalize()
    df = (
        df.groupby("date")[["cotacaoCompra", "cotacaoVenda"]]
          .last()
          .rename(columns={"cotacaoCompra": "buy", "cotacaoVenda": "sell"})
    )
    df["mid"] = (df["buy"] + df["sell"]) / 2
    return df.sort_index()


# ── ECB (EUR/USD) ─────────────────────────────────────────────────────────────

def fetch_ecb_eurusd(start: str = "2010-01-01") -> pd.DataFrame | None:
    """EUR/USD via ECB Statistical Data Warehouse — sem chave de API."""
    url = (
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
        f"?format=csvdata&startPeriod={start}"
    )
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  erro ECB: {e}")
        return None

    from io import StringIO
    df = pd.read_csv(StringIO(r.text))

    # ECB CSV tem muitas colunas — só precisamos de DATE e OBS_VALUE
    df.columns = [c.strip() for c in df.columns]
    df = df[["TIME_PERIOD", "OBS_VALUE"]].rename(
        columns={"TIME_PERIOD": "date", "OBS_VALUE": "close"}
    )
    df["date"]  = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.set_index("date").sort_index().dropna()


# ── FRED ──────────────────────────────────────────────────────────────────────

def fetch_fred(series_id: str, api_key: str, start: str = "2010-01-01") -> pd.DataFrame | None:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":          series_id,
        "api_key":            api_key,
        "file_type":          "json",
        "observation_start":  start,
        "sort_order":         "asc",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        obs = r.json().get("observations", [])
    except Exception as e:
        print(f"  erro FRED ({series_id}): {e}")
        return None

    if not obs:
        return None

    df = pd.DataFrame(obs)[["date", "value"]]
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.rename(columns={"value": "close"})
    return df.set_index("date").sort_index().dropna()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fred_key = os.getenv("FRED_API_KEY")
    sheets = {}

    print("=== PTAX USD/BRL (BCB) ===")
    df = fetch_ptax()
    if df is not None:
        sheets["PTAX_USDBRL"] = df
        print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
              f"último mid: {df['mid'].iloc[-1]:.4f}")

    print("\n=== EUR/USD (ECB) ===")
    df = fetch_ecb_eurusd()
    if df is not None:
        sheets["EUR_USD"] = df
        print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
              f"último: {df['close'].iloc[-1]:.4f}")

    if not fred_key:
        print("\nAVISO: FRED_API_KEY não configurada — CNY/USD, DXY e US10Y ignorados")
        print("       Obtenha uma chave gratuita em: https://fred.stlouisfed.org/docs/api/api_key.html")
    else:
        for name, series in FRED_SERIES.items():
            print(f"\n=== {name} (FRED: {series}) ===")
            df = fetch_fred(series, fred_key)
            if df is not None:
                sheets[name] = df
                print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
                      f"último: {df['close'].iloc[-1]:.4f}")

    print("\n=== DI Fut Jan/XX (B3) ===")
    print("  TODO: fonte não implementada (B3/ANBIMA sem API pública estável)")

    if not sheets:
        print("Nenhum dado coletado.")
        return

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31])
    print("Pronto.")


if __name__ == "__main__":
    main()
