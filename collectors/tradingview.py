"""
Curva futura via TradingView scanner API.
Atualiza base histórica em BD_FUTUROS.xlsx (formato long).
"""

import os
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import requests

BD_FUTUROS_PATH = Path(r"C:/Users/xanme/OneDrive/DERROND/FERRAMENTAS/BASES/BD_FUTUROS.xlsx")
SHEET_NAME = "BD_FUTUROS"

# Ativos relevantes para o relatório semanal
ATIVOS = {
    "LME":        ["CA", "AH"],   # Cobre, Alumínio
    "SHFE":       ["CU", "AL", "HC"],  # Cobre, Alumínio, HRC
    "BMFBOVESPA": ["DI1"],        # DI Futuro (juros Brasil)
}

COLUMNS = ["DATA_REF", "ATIVO_ID", "EXCHANGE", "CONTRATO", "VENCIMENTO", "PRECO", "CURRENCY", "IS_SPOT"]


def get_futures(exchange: str, ticker: str) -> list:
    root = f"{exchange}:{ticker}"
    url = "https://scanner.tradingview.com/futures/scan?label-product=futures-forward-curve"
    payload = {
        "columns": ["expiration", "close", "name", "currency"],
        "filter": [
            {"left": "close",      "operation": "nempty"},
            {"left": "expiration", "operation": "nempty"},
        ],
        "ignore_unknown_fields": False,
        "sort": {"sortBy": "expiration", "sortOrder": "asc"},
        "markets": ["futures"],
        "index_filters": [{"name": "root", "values": [root]}],
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json().get("data", [])


def build_rows(exchange: str, ticker: str, data_ref: date, max_points: int = 36) -> list[dict]:
    rows = get_futures(exchange, ticker)[:max_points]
    if not rows:
        print(f"  >> Sem dados para {exchange}:{ticker}")
        return []

    ativo_id = f"{exchange}-{ticker}"
    resultado = []
    for i, row in enumerate(rows):
        exp_int, close, code, ccy = row["d"]
        vencimento = datetime.strptime(str(exp_int), "%Y%m%d").date()
        resultado.append({
            "DATA_REF":   data_ref,
            "ATIVO_ID":   ativo_id,
            "EXCHANGE":   exchange,
            "CONTRATO":   code,
            "VENCIMENTO": vencimento,
            "PRECO":      float(close),
            "CURRENCY":   ccy,
            "IS_SPOT":    1 if i == 0 else 0,
        })
    return resultado


def data_referencia() -> date:
    hoje = datetime.today()
    wd = hoje.weekday()
    if wd == 0:   return (hoje - timedelta(days=3)).date()
    if wd in (5, 6): return (hoje - timedelta(days=wd - 4)).date()
    return (hoje - timedelta(days=1)).date()


def atualizar_bd_futuros(max_points: int = 36):
    data_ref = data_referencia()
    print(f"Data de referência: {data_ref}")

    novas_linhas = []
    for exchange, tickers in ATIVOS.items():
        for ticker in tickers:
            print(f"  {exchange}:{ticker}...", end=" ", flush=True)
            linhas = build_rows(exchange, ticker, data_ref, max_points)
            print(f"{len(linhas)} contratos")
            novas_linhas.extend(linhas)

    if not novas_linhas:
        print("Nenhuma linha nova.")
        return

    df_novo = pd.DataFrame(novas_linhas)[COLUMNS]

    if BD_FUTUROS_PATH.exists():
        try:
            df_existente = pd.read_excel(BD_FUTUROS_PATH, sheet_name=SHEET_NAME)
            df_existente["DATA_REF"]   = pd.to_datetime(df_existente["DATA_REF"]).dt.date
            df_existente["VENCIMENTO"] = pd.to_datetime(df_existente["VENCIMENTO"]).dt.date
        except Exception as e:
            print(f"Aviso: base existente ilegível, recriando. ({e})")
            df_existente = pd.DataFrame(columns=COLUMNS)
    else:
        BD_FUTUROS_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_existente = pd.DataFrame(columns=COLUMNS)

    df_all = pd.concat([df_existente, df_novo], ignore_index=True)
    df_all["DATA_REF"]   = pd.to_datetime(df_all["DATA_REF"]).dt.date
    df_all["VENCIMENTO"] = pd.to_datetime(df_all["VENCIMENTO"]).dt.date
    df_all.drop_duplicates(subset=["DATA_REF", "ATIVO_ID", "CONTRATO"], keep="last", inplace=True)
    df_all.sort_values(by=["DATA_REF", "ATIVO_ID", "VENCIMENTO"], inplace=True)

    with pd.ExcelWriter(BD_FUTUROS_PATH, engine="openpyxl", mode="w") as writer:
        df_all.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    print(f"BD_FUTUROS atualizado: {len(df_all)} linhas totais.")


if __name__ == "__main__":
    atualizar_bd_futuros()
