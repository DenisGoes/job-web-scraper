# from app.scrapers.infojobs.scraper import run_scraper_infojobs
from app.scrapers.linkdin.scraper import run_scraper_linkdin
from app.services.telegram import enviar_novas_vagas



def main():
    # run_scraper_infojobs()
    run_scraper_linkdin()
    enviar_novas_vagas()


if __name__ == "__main__":
    main()