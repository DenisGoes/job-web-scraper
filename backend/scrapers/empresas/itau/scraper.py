from playwright.sync_api import sync_playwright
from backend.database.crud.crud_vaga import salvar_vaga
from backend.scrapers.filtros import safe_text
import time

BASE_URL = "https://carreiras.itau.com.br"


def run_scraper_itau():

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"],
        )

        context = browser.new_context()

        page = context.new_page()
        page.set_default_timeout(30000)

        page.goto(
            "https://carreiras.itau.com.br/busca-de-vagas",
            wait_until="domcontentloaded",
        )
        page.wait_for_selector(".results__item", timeout=30000)

        cards = page.locator(".results__item")

        total_cards = cards.count()
        print(f"  -> {total_cards} vagas encontradas nesta página")

        for i in range(total_cards):
            try:
                card = cards.nth(i)

                # O <a> com data-job-id e href está dentro do card
                link_el = card.locator("a.results__item-link")

                titulo = safe_text(link_el.locator("h2.results__item-heading"))

                vaga_id = link_el.get_attribute("data-job-id")

                empresa = "Itaú"

                localidade = safe_text(link_el.locator(".job-location"))

                href = link_el.get_attribute("href")
                link_vaga = f"{BASE_URL}{href}" if href else "N/A"

                mensagem = (
                    "🔥 <b>Nova vaga no Itaú!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {empresa}\n"
                    f"📍 {localidade}\n"
                    f"🔗 {link_vaga}"
                )

                print(f"""
                    Titulo: {titulo}
                    Empresa: {empresa}
                    Localidade: {localidade}
                    Link: {link_vaga}
                    Salvando vaga no banco... {vaga_id}
                    """)

                salvar_vaga(
                    vaga_id=vaga_id,
                    fonte="itau",
                    titulo=titulo,
                    empresa=empresa,
                    localidade=localidade,
                    link_vaga=link_vaga,
                    mensagem=mensagem,
                )

            except Exception as e:
                print(f"Um erro inesperado aconteceu! {e}")

        time.sleep(3)

        browser.close()