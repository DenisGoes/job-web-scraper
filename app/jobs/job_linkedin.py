from app.scrapers.linkedin_scraper import LinkedinScraper
from app.integrations.telegram.telegram import enviar_novas_vagas


def main():
    scraper = LinkedinScraper("linkedin")
    scraper.executar()

    enviar_novas_vagas()


if __name__ == "__main__":
    main()