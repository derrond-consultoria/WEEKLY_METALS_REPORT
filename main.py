from dotenv import load_dotenv

load_dotenv()


def run():
    from collectors import lme, comex, shfe, energy_pvc, iron_ore, fx_rates, tradingview, cftc

    print("=== Weekly Metals Report ===\n")
    lme.main()
    comex.main()
    shfe.main()
    energy_pvc.main()
    iron_ore.main()
    fx_rates.main()
    tradingview.atualizar_bd_futuros()
    cftc.main()


if __name__ == "__main__":
    run()
