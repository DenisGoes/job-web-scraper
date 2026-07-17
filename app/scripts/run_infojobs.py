from app.scrapers.infojobs.scraper import run_scraper_infojobs
from app.services.telegram import enviar_novas_vagas


def main():
    run_scraper_infojobs()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()