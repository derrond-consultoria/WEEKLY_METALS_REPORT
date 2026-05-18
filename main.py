from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
import pandas as pd

BD_SEMANAL = Path(__file__).parent / "data" / "BD_SEMANAL.xlsx"

GRUPOS = [
    ("Preços Históricos",  ["lme", "shfe", "energy_pvc", "iron_ore", "fx_rates"]),
    ("Curvas Futuras",     ["tradingview"]),
    ("Posição de Fundos",  ["cftc"]),
]


def run():
    import importlib
    all_sheets: dict[str, pd.DataFrame] = {}

    for grupo, modulos in GRUPOS:
        print(f"\n{'='*55}")
        print(f"  {grupo}")
        print(f"{'='*55}")
        for mod_name in modulos:
            mod = importlib.import_module(f"collectors.{mod_name}")
            sheets = mod.collect()
            all_sheets.update(sheets)

    BD_SEMANAL.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nSalvando BD_SEMANAL.xlsx ({len(all_sheets)} abas)...")
    with pd.ExcelWriter(BD_SEMANAL, engine="openpyxl") as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31])

    print(f"Pronto: {BD_SEMANAL}")
    print("\nAbas geradas:")
    for name in all_sheets:
        print(f"  • {name}")


if __name__ == "__main__":
    run()