# Weekly Metals Report

Coleta automatizada de preços e indicadores para relatório semanal de metais.

## Estrutura

```
WEEKLY_METALS_REPORT/
├── collectors/
│   ├── lme.py          Cobre & Alumínio LME — histórico (Westmetall)
│   ├── comex.py        Cobre & Alumínio COMEX — histórico (Stooq)
│   ├── shfe.py         Aço HRC SHFE — histórico (akshare)
│   ├── energy_pvc.py   Brent (Stooq) + PVC DCE (akshare)
│   ├── iron_ore.py     Minério de Ferro 62% Fe DCE (akshare)
│   ├── tradingview.py  Curvas futuras LME/SHFE (TradingView API)
│   ├── fx_rates.py     PTAX, EUR/USD, CNY/USD, DXY, US10Y, DI Fut (BCB + Stooq)
│   └── cftc.py         CFTC Managed Money (Nasdaq Data Link)
├── data/               Outputs locais — gitignored
├── .env.example        Template de variáveis de ambiente
├── requirements.txt
└── main.py
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# editar .env com NASDAQ_API_KEY
```

## Executar coletor individual

```bash
python -m collectors.lme
python -m collectors.fx_rates
# etc.
```
