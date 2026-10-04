from app.scrapers.base_scraper import BaseScraper
from app.model.vaga import Vaga
from app.scrapers.filtros import safe_text
from urllib.parse import urljoin

class BradescoScraper(BaseScraper):

    def executar(self):

        self.iniciar_navegador()

        try:
            self.page.goto(
                "https://bradesco.csod.com/ux/ats/careersite/1/home?c=bradesco&cfdd[0][id]=127&cfdd[0][options][0]=69&cfdd[0][options][1]=70&cfdd[1][id]=634&cfdd[1][options][0]=1429&country=br&state=sp&city=osasco",
                wait_until="domcontentloaded",
            )

            self.page.wait_for_selector('[data-tag="displayJobTitle"]',timeout=30000)

            titulos = self.page.locator('[data-tag="displayJobTitle"]')

            total_cards = titulos.count()

            print(f"-> {total_cards} vagas encontradas")

            for i in range(total_cards):
                try:
                    titulo_el = titulos.nth(i)
                    
                    card = titulo_el.locator("xpath=ancestor::div[contains(@class, 'p-panel')][1]")

                    titulo = safe_text(titulo_el)
                    vaga_id = titulo_el.locator("p").get_attribute("data-tag")
                    empresa = "Bradesco"
                    localidade = safe_text(card.locator('[data-tag="displayJobLocation"]'))
                    href = titulo_el.get_attribute("href")
                    link_vaga = urljoin(
                        self.page.url,
                        href
                    ) if href else None
                    data = safe_text(card.locator('[data-tag="displayJobPostingDate"]'))

                    mensagem = (
                        "🔥 <b>Nova vaga no Bradesco!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"📅 {data}\n"
                        f"🔗 {link_vaga}"
                    )

                    print(
                        f"""
                        ID: {vaga_id}
                        Título: {titulo}
                        Empresa: {empresa}
                        Localidade: {localidade}
                        Link: {link_vaga}
                        Data: {data}
                        """
                    )

                    vaga = Vaga(
                        vaga_id=vaga_id,
                        fonte=self.fonte,
                        titulo=titulo,
                        empresa=empresa,
                        localidade=localidade,
                        link_vaga=link_vaga,
                        data_publicacao=data,
                        mensagem=mensagem
                    )

                    self.salvar_vaga(vaga)

                except Exception as e:
                    print(f"Erro ao processar vaga {i}: {e}")

        finally:
            self.fechar_navegador()