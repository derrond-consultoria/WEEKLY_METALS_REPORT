"""
Câmbio e Juros — séries históricas diárias.

Fontes:
  USD/BRL PTAX  → API Banco Central do Brasil (gratuita, sem chave)
  CNY/USD       → Stooq (usdcny.fx invertido)
  EUR/USD       → Stooq (eurusd.fx)
  DXY           → Stooq (dxy.indx)
  US Treasury 10Y → Stooq (10us.b)
  DI Fut Jan/XX → B3 via stooq (di1f.b3) — vencimento mais próximo
"""

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "fx_rates.xlsx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Stooq tickers
STOOQ_TICKERS = {
    "USD_CNY":    "usdcny.fx",   # USD por CNY (inverte para CNY/USD)
    "EUR_USD":    "eurusd.fx",
    "DXY":        "dxy.indx",
    "US10Y":      "10us.b",
    "DI_FUT":     "di1f.b3",     # DI Futuro jan vencimento mais próximo (B3)
}


# ── Stooq ─────────────────────────────────────────────────────────────────────

def fetch_stooq(symbol: str) -> pd.DataFrame | None:
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  erro HTTP ({symbol}): {e}")
        return None

    text = r.text.strip()
    if not text or text.lower().startswith("no data"):
        print(f"  sem dados Stooq para {symbol}")
        return None

    df = pd.read_csv(StringIO(text))
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


# ── PTAX (Banco Central do Brasil) ────────────────────────────────────────────

def fetch_ptax(start: str = "01-01-2010") -> pd.DataFrame | None:
    """
    Cotação de fechamento PTAX USD/BRL via API pública do BCB.
    start: formato MM-DD-YYYY (padrão da API do BCB)
    """
    from datetime import datetime
    end = datetime.today().strftime("%m-%d-%Y")

    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarPeriodo(dataInicial=@di,dataFinalCotacao=@df)"
        f"?@di='{start}'&@df='{end}'&$format=json&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao"
    )

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json().get("value", [])
    except Exception as e:
        print(f"  erro PTAX: {e}")
        return None

    if not data:
        print("  PTAX: sem dados retornados")
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sheets = {}

    print("=== PTAX USD/BRL (BCB) ===")
    df_ptax = fetch_ptax()
    if df_ptax is not None:
        sheets["PTAX_USDBRL"] = df_ptax
        print(f"  {df_ptax.index.min().date()} -> {df_ptax.index.max().date()}  "
              f"último mid: {df_ptax['mid'].iloc[-1]:.4f}")

    for name, symbol in STOOQ_TICKERS.items():
        print(f"\n=== {name} ({symbol}) ===")
        df = fetch_stooq(symbol)
        if df is not None:
            sheets[name] = df
            print(f"  {df.index.min().date()} -> {df.index.max().date()}  "
                  f"último close: {df['close'].iloc[-1]:.4f}")

    if not sheets:
        print("Nenhum dado coletado.")
        return

    print(f"\nSalvando em {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31])

    print("Pronto.")


if __name__ == "__main__":
    main()
