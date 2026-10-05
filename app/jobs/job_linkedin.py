from app.scrapers.linkedin_scraper import LinkedinScraper
from app.services.telegram.telegram_service import enviar_novas_vagas


def main():
    scraper = LinkedinScraper("linkedin")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()