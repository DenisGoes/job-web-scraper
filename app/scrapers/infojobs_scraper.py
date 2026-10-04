import os
import json
import time
from app.config.settings import INFOJOBS_LOG
from app.scrapers.base_scraper import BaseScraper
from app.model.vaga import Vaga
from app.scrapers.filtros import (
    safe_text,
    titulo_relevante,
    descricao_relevante,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COOKIES_PATH = os.path.join(BASE_DIR, "cookies")

os.makedirs(COOKIES_PATH, exist_ok=True)


def close_popups(page):
    try:
        modal = page.locator("#modalPremiumDestaque")

        modal.wait_for(
            state="visible",
            timeout=5000
        )

        close_button = page.get_by_role(
            "link",
            name="Agora não"
        )

        close_button.click()

        print("Fechando popup...")

    except Exception as e:
        print(f"Erro ao fechar modal: {e}")


class InfojobsScraper(BaseScraper):

    def executar(self):
        if INFOJOBS_LOG:
            storage_state = json.loads(
                INFOJOBS_LOG
            )
        else:
            storage_state = os.path.join(
                BASE_DIR,
                "cookies",
                "infojobslog.json"
            )

        self.iniciar_navegador(
            storage_state=storage_state
        )

        try:
            self.page.goto(
                "https://www.infojobs.com.br/vagas-de-emprego-desenvolvimento+de+software-em-sao-paulo,-sp.aspx?categoria=74&sprd=25&splat=-23.48922&splng=-46.8059&tipocontrato=2,4,15&wo=1,2,5&im=1,4,5,6",
                wait_until="domcontentloaded",
            )

            self.page.wait_for_selector(".js_vacancyLoad",timeout=30000)

            close_popups(self.page)

            cards = self.page.locator(".js_vacancyLoad")

            max_vagas = 25

            total_cards = min(cards.count(),max_vagas)

            print(f"-> {total_cards} vagas encontradas nesta página")

            for i in range(total_cards):
                try:
                    card = cards.nth(i)

                    titulo = safe_text(card.locator(".js_vacancyTitle"))

                    if not titulo_relevante(titulo):
                        continue

                    descricao_locator = self.page.locator("div.text-medium").first

                    descricao_locator.wait_for(state="visible", timeout=10000)
                    descricao = descricao_locator.text_content()

                    if not descricao_relevante(descricao):
                        continue

                    vaga_id = card.get_attribute("data-id")
                    empresa = safe_text(card.locator("div.text-body a"))
                    localidade = safe_text(card.locator(".mb-8").first)
                    salario = safe_text(card.locator(".icon-money").locator("xpath=.."))
                    modelo_trabalho = safe_text(card.locator(".icon-buildings").locator("xpath=.."))
                    link_vaga = card.locator("a:has(h2.js_vacancyTitle)").evaluate("el => el.href")
                    data = safe_text(card.locator( ".small.text-nowrap"))

                    mensagem = (
                        "🔥 <b>Nova vaga no InfoJobs!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"{salario}\n"
                        f"{modelo_trabalho}\n"
                        f"📅 {data}\n"
                        f"🔗 {link_vaga}"
                    )

                    print(f"""
                        Título: {titulo}
                        Empresa: {empresa}
                        Localidade: {localidade}
                        Salário: {salario}
                        Modelo de trabalho: {modelo_trabalho}
                        Link: {link_vaga}
                        Data: {data}
                        Salvando vaga no banco... {vaga_id}
                        """)

                    vaga = Vaga(
                        vaga_id=vaga_id,
                        fonte=self.fonte,
                        titulo=titulo,
                        empresa=empresa,
                        localidade=localidade,
                        salario=salario,
                        modelo_trabalho=modelo_trabalho,
                        link_vaga=link_vaga,
                        data_publicacao=data,
                        mensagem=mensagem,
                        descricao=descricao,
                    )

                    self.salvar_vaga(vaga)

                except Exception as e:
                    print(f"Um erro inesperado aconteceu! {e}")

        finally:
            self.fechar_navegador()