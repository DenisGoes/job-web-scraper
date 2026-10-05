from app.scrapers.bradesco_scraper import BradescoScraper
from app.services.telegram.telegram_service import enviar_novas_vagas


def main():
    scraper = BradescoScraper("bradesco")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()