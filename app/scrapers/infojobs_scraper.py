import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page

from app.database.repository import salvar_vaga
from app.scrapers.base_scraper import (
    fechar_navegador,
    iniciar_navegador,
    rolar_ate_estabilizar,
)
from app.scrapers.filtros import (
    calcular_aderencia_stack,
    descricao_relevante,
    safe_text,
    titulo_relevante,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RAIZ_PROJETO = Path.cwd()
DESCRICAO_SELECTOR = "p.mb-16.text-break.white-space-pre-line, div.text-medium"


def registrar_fechamento_popups(page: Page) -> None:
    modal_premium = page.locator("#modalPremiumDestaque")
    page.add_locator_handler(
        modal_premium,
        lambda: modal_premium.locator(".modal-premium-popup-dismiss, [data-dismiss='modal']").first.click(),
    )

    banner_cookies = page.locator("#didomi-notice-agree-button, button:has-text('Aceitar e fechar')")
    page.add_locator_handler(
        banner_cookies,
        lambda: banner_cookies.first.click(),
    )


def fechar_popup_se_visivel(page: Page) -> None:
    try:
        modal = page.locator("#modalPremiumDestaque")
        if modal.is_visible(timeout=2500):
            modal.locator(".modal-premium-popup-dismiss, [data-dismiss='modal']").first.click()
            modal.wait_for(state="hidden", timeout=5000)
            print("Pop-up Premium fechado.")
    except Exception:
        pass


def executar_infojobs_scraper(max_vagas: int = 60, headless: bool = False) -> None:
    fonte = "InfoJobs"

    origem_sessao = os.getenv("INFOJOBS_LOG")
    if not origem_sessao:
        for candidato in [
            RAIZ_PROJETO / "infojobslog.json",
            BASE_DIR / "cookies" / "infojobslog.json",
        ]:
            if candidato.is_file():
                origem_sessao = str(candidato)
                break

    playwright, browser, context, page = iniciar_navegador(
        storage_state=origem_sessao,
        headless=headless,
    )

    try:
        registrar_fechamento_popups(page)

        page.goto("https://www.infojobs.com.br/", wait_until="domcontentloaded")
        time.sleep(random.uniform(3.0, 5.0))
        fechar_popup_se_visivel(page)

        page.goto(
            "https://www.infojobs.com.br/vagas-de-emprego-desenvolvimento+de+software-em-sao-paulo,-sp.aspx?categoria=70,74,83&Antiguedad=5",
            wait_until="domcontentloaded",
        )
        time.sleep(random.uniform(2.0, 3.5))
        fechar_popup_se_visivel(page)

        cards = rolar_ate_estabilizar(
            page,
            ".js_vacancyLoad",
            max_scrolls=20,
            timeout_inicial=20000,
        )
        total_cards = min(cards.count(), max_vagas)
        print(f"  -> {total_cards} vagas encontradas nesta página")

        for i in range(total_cards):
            try:
                card = cards.nth(i)
                card.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.7, 1.4))

                titulo = safe_text(card.locator(".js_vacancyTitle"))
                if not titulo_relevante(titulo):
                    print(f"Título rejeitado pelo filtro: {titulo}")
                    continue

                card.click()
                time.sleep(random.uniform(1.2, 2.2))

                descricao_locator = page.locator("p.mb-16.text-break.white-space-pre-line").first
                if descricao_locator.count() == 0:
                    descricao_locator = page.locator(DESCRICAO_SELECTOR).first

                descricao_locator.wait_for(state="visible", timeout=10000)

                descricao = descricao_locator.inner_text() or ""
                if not descricao_relevante(descricao):
                    print(f"Descrição rejeitada pelo filtro: {titulo}")
                    continue

                vaga_id = card.get_attribute("data-id")
                empresa = safe_text(card.locator("div.text-body a, div.text-body span").first)
                localidade = safe_text(card.locator(".mb-8").first)
                salario = safe_text(card.locator(".icon-money").locator("xpath=.."))
                modelo_trabalho = safe_text(card.locator(".icon-buildings").locator("xpath=.."))
                link_vaga = card.locator("a:has(h2.js_vacancyTitle)").evaluate("el => el.href")
                data = safe_text(card.locator(".small.text-nowrap"))

                if not vaga_id or not link_vaga:
                    print(f"Vaga {i} ignorada: ID ou link ausente.")
                    continue

                skills_match = calcular_aderencia_stack(titulo, descricao)
                linha_stack = f"🛠 <b>Stack:</b> {', '.join(skills_match)}\n" if skills_match else ""

                mensagem = (
                    "🔥 <b>Nova vaga no InfoJobs!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {empresa}\n"
                    f"📍 {localidade}\n"
                    f"{linha_stack}"
                    f"💰 {salario}\n"
                    f"💼 {modelo_trabalho}\n"
                    f"📅 {data}\n"
                    f"🔗 {link_vaga}"
                )

                print(
                    f"""
                    Título: {titulo}
                    Empresa: {empresa}
                    Localidade: {localidade}
                    Stack: {', '.join(skills_match) if skills_match else 'Geral Tech'}
                    Salário: {salario}
                    Modelo de trabalho: {modelo_trabalho}
                    Link: {link_vaga}
                    Data: {data}
                    Salvando vaga no banco... {vaga_id}
                    """
                )

                salvar_vaga(
                    vaga_id=vaga_id,
                    fonte=fonte,
                    titulo=titulo,
                    empresa=empresa,
                    localidade=localidade,
                    salario=salario,
                    modelo_trabalho=modelo_trabalho,
                    link_vaga=link_vaga,
                    data_publicacao=data,
                    mensagem=mensagem,
                )

            except Exception as e:
                print(f"Erro ao processar vaga {i} no InfoJobs: {e}")

        time.sleep(random.uniform(2.5, 4.0))

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    executar_infojobs_scraper(max_vagas=60, headless=True)