from playwright.sync_api import sync_playwright
from backend.scrapers.filtros import safe_text
from backend.database.crud.crud_vaga import salvar_vaga
import time


def run_scraper_bradesco():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

        context = browser.new_context()
        page = context.new_page()

        page.set_default_timeout(30000)

        page.goto(
            "https://bradesco.csod.com/ux/ats/careersite/1/home?c=bradesco&cfdd[0][id]=127&cfdd[0][options][0]=69&cfdd[0][options][1]=70&cfdd[1][id]=634&cfdd[1][options][0]=1429&country=br&state=sp&city=osasco",
            wait_until="domcontentloaded",
        )

        # Aguarda os cards carregarem
        page.wait_for_selector('[data-tag="displayJobTitle"]', timeout=30000)

        # Ancora em cada título (elemento único), não no painel
        # (o .p-panel pode se repetir/aninhar e casar com vários títulos ao mesmo tempo)
        titulos = page.locator('[data-tag="displayJobTitle"]')

        total_cards = titulos.count()

        print(f"-> {total_cards} vagas encontradas")

        for i in range(total_cards):

            try:
                titulo_el = titulos.nth(i)

                # Sobe até o .p-panel ancestral MAIS PRÓXIMO deste título específico
                card = titulo_el.locator(
                    "xpath=ancestor::div[contains(@class, 'p-panel')][1]"
                )

                # IMPORTANTE: passar o locator puro para safe_text,
                # nunca chamar .inner_text()/.text_content() antes
                titulo = safe_text(titulo_el)

                # O <p> dentro do <a> carrega o ID numérico da vaga no atributo data-tag
                vaga_id = titulo_el.locator("p").get_attribute("data-tag")

                empresa = "Bradesco"

                localidade = safe_text(
                    card.locator('[data-tag="displayJobLocation"]')
                )

                link_vaga = titulo_el.get_attribute("href")

                data = safe_text(
                    card.locator('[data-tag="displayJobPostingDate"]')
                )

                mensagem = (
                    "🔥 <b>Nova vaga no Bradesco!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {empresa}\n"
                    f"📍 {localidade}\n"
                    f"📅 {data}\n"
                    f"🔗 {link_vaga}"
                )

                print(f"""
                    ID: {vaga_id}
                    Título: {titulo}
                    Empresa: {empresa}
                    Localidade: {localidade}
                    Link: {link_vaga}
                    Data: {data}
                """)

                # Salva a vaga no banco de dados.
                salvar_vaga(
                    vaga_id=vaga_id,
                    fonte="Bradesco",
                    titulo=titulo,
                    empresa=empresa,
                    localidade=localidade,
                    link_vaga=link_vaga,
                    data_publicacao=data,
                    mensagem=mensagem
                )

            except Exception as e:
                print(f"Erro ao processar vaga: {e}")

                time.sleep(3)

        browser.close()