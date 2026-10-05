from app.scrapers.infojobs_scraper import InfojobsScraper
from app.services.telegram.telegram_service import enviar_novas_vagas


def main():
    scraper = InfojobsScraper("infoJobs")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()