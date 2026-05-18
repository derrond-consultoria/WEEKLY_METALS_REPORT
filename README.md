# Weekly Metals Report

Coleta automatizada de dados de metais (Au, Ag, Cu, Fe, Al, Ni, Zn, Pb, Sn, etc.) via APIs, web scraping e bases de dados para geração de relatório semanal.

## Estrutura

```
WEEKLY_METALS_REPORT/
├── collectors/        # Scripts de coleta por fonte
│   ├── apis/          # Integrações com APIs (Alpha Vantage, LME, etc.)
│   ├── scrapers/      # Web scraping
│   └── databases/     # Consultas a bases de dados externas
├── processors/        # Transformação e limpeza dos dados
├── reports/
│   ├── templates/     # Templates Jinja2 (HTML/PDF)
│   └── generated/     # Relatórios gerados (gitignored)
├── data/
│   ├── raw/           # Dados brutos (gitignored)
│   ├── processed/     # Dados tratados
│   └── samples/       # Amostras de referência (versionadas)
├── logs/              # Logs de execução (gitignored)
├── .env.example       # Variáveis de ambiente (template público)
├── requirements.txt
└── main.py            # Entrypoint semanal
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env
# editar .env com suas chaves
```

## Execução

```bash
python main.py
```
