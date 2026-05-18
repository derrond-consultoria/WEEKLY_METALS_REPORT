"""
Curva futura via TradingView scanner API.
Atualiza BD_FUTUROS.xlsx (formato long, acumulativo) e expõe
snapshot do dia para o BD_SEMANAL via collect().
"""

from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import requests

BD_FUTUROS_PATH = Path(__file__).parent.parent / "data" / "BD_FUTUROS.xlsx"
SHEET_NAME = "BD_FUTUROS"

ATIVOS = {
    "LME":        ["CA", "AH"],        # Cobre, Alumínio
    "SHFE":       ["CU", "AL", "HC"],  # Cobre, Alumínio, HRC
    "BMFBOVESPA": ["DI1"],             # DI Futuro (juros Brasil)
}

COLUMNS = ["DATA_REF", "ATIVO_ID", "EXCHANGE", "CONTRATO", "VENCIMENTO", "PRECO", "CURRENCY", "IS_SPOT"]

# Mapeamento ATIVO_ID → nome da aba no BD_SEMANAL
CURVE_SHEETS = {
    "LME-CA":         "Curva_LME_Cu",
    "LME-AH":         "Curva_LME_Al",
    "SHFE-HC":        "Curva_SHFE_HRC",
    "BMFBOVESPA-DI1": "Curva_DI1",
}


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
    if wd == 0:      return (hoje - timedelta(days=3)).date()
    if wd in (5, 6): return (hoje - timedelta(days=wd - 4)).date()
    return (hoje - timedelta(days=1)).date()


def atualizar_bd_futuros(max_points: int = 36) -> pd.DataFrame:
    """Coleta curvas do dia, persiste em BD_FUTUROS.xlsx e retorna o DataFrame completo."""
    data_ref = data_referencia()
    print(f"\n=== Curvas Futuras (TradingView) — ref: {data_ref} ===")

    novas_linhas = []
    for exchange, tickers in ATIVOS.items():
        for ticker in tickers:
            print(f"  {exchange}:{ticker}...", end=" ", flush=True)
            linhas = build_rows(exchange, ticker, data_ref, max_points)
            print(f"{len(linhas)} contratos")
            novas_linhas.extend(linhas)

    if not novas_linhas:
        print("  Nenhuma linha nova.")
        return pd.DataFrame(columns=COLUMNS)

    df_novo = pd.DataFrame(novas_linhas)[COLUMNS]

    BD_FUTUROS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if BD_FUTUROS_PATH.exists():
        try:
            df_existente = pd.read_excel(BD_FUTUROS_PATH, sheet_name=SHEET_NAME)
            df_existente["DATA_REF"]   = pd.to_datetime(df_existente["DATA_REF"]).dt.date
            df_existente["VENCIMENTO"] = pd.to_datetime(df_existente["VENCIMENTO"]).dt.date
        except Exception as e:
            print(f"  Aviso: base ilegível, recriando. ({e})")
            df_existente = pd.DataFrame(columns=COLUMNS)
    else:
        df_existente = pd.DataFrame(columns=COLUMNS)

    df_all = pd.concat([df_existente, df_novo], ignore_index=True)
    df_all["DATA_REF"]   = pd.to_datetime(df_all["DATA_REF"]).dt.date
    df_all["VENCIMENTO"] = pd.to_datetime(df_all["VENCIMENTO"]).dt.date
    df_all.drop_duplicates(subset=["DATA_REF", "ATIVO_ID", "CONTRATO"], keep="last", inplace=True)
    df_all.sort_values(by=["DATA_REF", "ATIVO_ID", "VENCIMENTO"], inplace=True)

    with pd.ExcelWriter(BD_FUTUROS_PATH, engine="openpyxl", mode="w") as writer:
        df_all.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    print(f"  BD_FUTUROS: {len(df_all)} linhas totais.")
    return df_all


def collect() -> dict[str, pd.DataFrame]:
    """Atualiza BD_FUTUROS e retorna snapshot do dia por instrumento."""
    df_all = atualizar_bd_futuros()
    if df_all.empty:
        return {}

    latest = df_all["DATA_REF"].max()
    df_hoje = df_all[df_all["DATA_REF"] == latest].copy()

    data = {}
    for ativo_id, sheet_name in CURVE_SHEETS.items():
        df = df_hoje[df_hoje["ATIVO_ID"] == ativo_id][
            ["VENCIMENTO", "CONTRATO", "PRECO", "CURRENCY"]
        ].reset_index(drop=True)
        if not df.empty:
            data[sheet_name] = df

    return data


if __name__ == "__main__":
    atualizar_bd_futuros()