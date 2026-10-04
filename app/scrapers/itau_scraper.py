from app.scrapers.base_scraper import BaseScraper
from app.model.vaga import Vaga
from app.scrapers.filtros import safe_text


BASE_URL = "https://carreiras.itau.com.br"


class ItauScraper(BaseScraper):

    def executar(self):
        self.iniciar_navegador()

        try:
            self.page.goto(f"{BASE_URL}/busca-de-vagas",wait_until="domcontentloaded",)

            self.page.wait_for_selector(".results__item",timeout=30000)

            cards = self.page.locator(".results__item")
            total_cards = cards.count()

            print(f"-> {total_cards} vagas encontradas nesta página")

            for i in range(total_cards):
                try:
                    card = cards.nth(i)

                    link_el = card.locator("a.results__item-link")
                    titulo = safe_text(link_el.locator("h2.results__item-heading"))
                    vaga_id = link_el.get_attribute("data-job-id")
                    empresa = "Itaú"
                    localidade = safe_text(link_el.locator(".job-location"))
                    href = link_el.get_attribute("href")
                    
                    link_vaga = (
                        f"{BASE_URL}{href}"
                        if href
                        else "N/A"
                    )

                    mensagem = (
                        "🔥 <b>Nova vaga no Itaú!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"🔗 {link_vaga}"
                    )

                    print(
                        f"""
                        Título: {titulo}
                        Empresa: {empresa}
                        Localidade: {localidade}
                        Link: {link_vaga}
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
                        mensagem=mensagem,
                    )

                    self.salvar_vaga(vaga)

                except Exception as e:
                    print(f"Erro ao processar vaga {i}: {e}")

        finally:
            self.fechar_navegador()