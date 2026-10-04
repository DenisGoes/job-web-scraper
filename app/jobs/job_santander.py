from app.scrapers.santander_scraper import SantanderScraper
from app.integrations.telegram.telegram import enviar_novas_vagas


def main():
    scraper = SantanderScraper("santander")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()