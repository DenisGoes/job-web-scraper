from urllib.parse import urljoin

from app.scrapers.base_scraper import BaseScraper
from app.model.vaga import Vaga
from app.scrapers.filtros import safe_text


BASE_URL = "https://santander.wd3.myworkdayjobs.com"


class SantanderScraper(BaseScraper):

    def executar(self):
        self.iniciar_navegador()

        try:
            self.page.goto(
                "https://santander.wd3.myworkdayjobs.com/pt-BR/SantanderCareers?locationCountry=1a29bb1357b240ab99a2fa755cc87c0e&locationRegionStateProvince=6177762425c54ca8aa31aac74fb08fad&jobFamilyGroup=ab9adf92110e01018e26d3aa1a01014a&jobFamilyGroup=135a3ebce38101c45b3e18b919012750&jobFamilyGroup=6cefe723149d01b7cf3faef619014f4b&jobFamilyGroup=135a3ebce3810166e65b0db919012550&jobFamilyGroup=047662461dfb01bf0a10a10a1a01d241&jobFamilyGroup=135a3ebce38101db91d599b919013150&jobFamilyGroup=ab9adf92110e0160f08437aa1a01f549",
                wait_until="domcontentloaded",
            )

            self.page.wait_for_selector(".css-1q2dra3",timeout=30000)

            cards = self.page.locator(".css-1q2dra3")

            total_cards = cards.count()

            print(f"-> {total_cards} vagas encontradas nesta página")

            for i in range(total_cards):
                try:
                    card = cards.nth(i)

                    titulo = safe_text(card.locator('[data-automation-id="jobTitle"]'))
                    vaga_id = safe_text(card.locator('[data-automation-id="subtitle"] li'))
                    empresa = "Santander"
                    localidade = safe_text(card.locator('[data-automation-id="locations"] dd'))
                    href = card.locator('[data-automation-id="jobTitle"]').get_attribute("href")
                    link_vaga = (
                        urljoin(BASE_URL, href)
                        if href
                        else None
                    )
                    data = safe_text(card.locator('[data-automation-id="postedOn"] dd'))

                    mensagem = (
                        "🔥 <b>Nova vaga no Santander!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"📅 {data}\n"
                        f"🔗 {link_vaga}"
                    )

                    print(
                        f"""
                        Título: {titulo}
                        Empresa: {empresa}
                        Localidade: {localidade}
                        Link: {link_vaga}
                        Data: {data}
                        Salvando vaga no banco... {vaga_id}
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
                        mensagem=mensagem,
                    )

                    self.salvar_vaga(vaga)

                except Exception as e:
                    print(f"Erro ao processar vaga {i}: {e}")

        finally:
            self.fechar_navegador()