from app.scrapers.itau_scraper import ItauScraper
from app.services.telegram.telegram_service import enviar_novas_vagas


def main():
    scraper = ItauScraper("itau")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()