from backend.scrapers.empresas.itau.scraper import run_scraper_itau
from backend.services.telegram import enviar_novas_vagas


def main():
    run_scraper_itau()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()