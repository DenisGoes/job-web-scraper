from backend.scrapers.empresas.santander.scraper import run_scraper_santander
from backend.services.telegram import enviar_novas_vagas


def main():
    run_scraper_santander()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()