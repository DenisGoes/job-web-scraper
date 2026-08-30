from backend.scrapers.empresas.bradesco.scraper import run_scraper_bradesco
from backend.services.telegram import enviar_novas_vagas


def main():
    run_scraper_bradesco()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()