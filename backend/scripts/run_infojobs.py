from backend.scrapers.fontes.infojobs.scraper import run_scraper_infojobs
from backend.services.telegram import enviar_novas_vagas


def main():
    run_scraper_infojobs()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()