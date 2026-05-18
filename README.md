# Weekly Metals Report

Coleta automatizada de preços, curvas futuras e posição de fundos para geração de relatório semanal de metais. Toda a saída é consolidada em um único arquivo `data/BD_SEMANAL.xlsx`.

## Estrutura

```
WEEKLY_METALS_REPORT/
├── collectors/
│   ├── lme.py          LME Cobre & Alumínio — histórico diário (Westmetall)
│   ├── shfe.py         Aço HRC SHFE — histórico diário (akshare)
│   ├── energy_pvc.py   Brent (EIA) + PVC DCE (akshare) — histórico diário
│   ├── iron_ore.py     Minério de Ferro 62% Fe DCE — histórico diário (akshare)
│   ├── fx_rates.py     PTAX (BCB), EUR/USD (ECB), CNY/USD + DXY + US10Y (FRED)
│   ├── tradingview.py  Curvas futuras LME/SHFE/DI1 (TradingView API)
│   └── cftc.py         CFTC Managed Money — Cobre, Alumínio, Brent (Nasdaq Data Link)
├── data/               Outputs — gitignored (regenerar via main.py)
│   ├── BD_SEMANAL.xlsx   Arquivo principal do relatório (18 abas)
│   └── BD_FUTUROS.xlsx   Banco acumulativo de curvas futuras
├── .env.example        Template de variáveis de ambiente
├── requirements.txt
└── main.py             Entrypoint — gera BD_SEMANAL.xlsx
```

## Saída — BD_SEMANAL.xlsx

| Grupo | Aba | Fonte | Frequência |
|---|---|---|---|
| Preços Históricos | `Preco_LME_Cu` | Westmetall | Diária |
| | `Preco_LME_Al` | Westmetall | Diária |
| | `Preco_SHFE_HRC` | akshare | Diária |
| | `Preco_Minerio_Fe` | akshare | Diária |
| | `Preco_Brent` | EIA API | Diária |
| | `Preco_PVC_DCE` | akshare | Diária |
| | `FX_PTAX` | Banco Central do Brasil | Diária |
| | `FX_EUR_USD` | ECB SDW | Diária |
| | `FX_CNY_USD` | FRED (`DEXCHUS`) | Diária |
| | `FX_DXY` | FRED (`DTWEXBGS`) | Diária |
| | `Juros_US10Y` | FRED (`DGS10`) | Diária |
| Curvas Futuras | `Curva_LME_Cu` | TradingView | Snapshot do dia |
| | `Curva_LME_Al` | TradingView | Snapshot do dia |
| | `Curva_SHFE_HRC` | TradingView | Snapshot do dia |
| | `Curva_DI1` | TradingView | Snapshot do dia |
| Posição de Fundos | `CFTC_Copper` | Nasdaq Data Link | Semanal |
| | `CFTC_Aluminium` | Nasdaq Data Link | Semanal |
| | `CFTC_Brent` | Nasdaq Data Link | Semanal |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Preencher as chaves no .env
```

## Variáveis de ambiente (`.env`)

| Variável | Uso | Obter em |
|---|---|---|
| `ALPHA_VANTAGE_API_KEY` | — (reservado) | alphavantage.co |
| `NASDAQ_API_KEY` | CFTC Managed Money | data.nasdaq.com |
| `EIA_API_KEY` | Brent histórico | eia.gov/opendata |
| `FRED_API_KEY` | CNY/USD, DXY, US10Y | fred.stlouisfed.org |

Fontes sem chave: Westmetall, akshare, BCB (PTAX), ECB (EUR/USD), TradingView.

## Execução

```bash
# Relatório completo → data/BD_SEMANAL.xlsx
python main.py

# Coletor individual (para teste)
python -m collectors.lme
python -m collectors.fx_rates
python -m collectors.tradingview
```