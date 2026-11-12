import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Locator, Page

from app.database.repository import salvar_vaga
from app.scrapers.base_scraper import fechar_navegador, iniciar_navegador
from app.scrapers.filtros import (
    calcular_aderencia_stack,
    descricao_relevante,
    safe_text,
    titulo_relevante,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RAIZ_PROJETO = Path.cwd()

CARD_SELECTOR = 'div[role="button"][componentkey^="job-card-component-ref-"]'
DESCRICAO_SELECTOR = 'span[data-testid="expandable-text-box"]'
NEXT_BUTTON_SELECTOR = 'button[data-testid="pagination-controls-next-button-visible"]'


def scroll_current_page(page: Page, max_scrolls: int = 20) -> Locator:
    print("Executando scroll humanizado...")

    page.wait_for_selector(CARD_SELECTOR, timeout=20000)
    cards = page.locator(CARD_SELECTOR)
    cards.first.hover()
    time.sleep(random.uniform(1.0, 2.0))

    vagas_antes = 0
    tentativas = 0

    while tentativas < max_scrolls:
        distancia = random.randint(650, 950)
        page.mouse.wheel(0, distancia)
        page.wait_for_timeout(int(random.uniform(1200, 2200)))

        vagas_agora = cards.count()
        if vagas_agora == vagas_antes:
            # Faz uma última confirmação com pausa maior antes de encerrar o scroll
            page.wait_for_timeout(int(random.uniform(1500, 2500)))
            if cards.count() == vagas_antes:
                break

        vagas_antes = vagas_agora
        tentativas += 1

    print(f"Scroll finalizado: {vagas_antes} vagas carregadas na tela.")
    return cards


def process_current_page(page: Page, cards: Locator, max_vagas_pagina: int = 50) -> None:
    total_cards = min(cards.count(), max_vagas_pagina)
    print(f"  -> {total_cards} vagas encontradas nesta página")

    for i in range(total_cards):
        try:
            card = cards.nth(i)
            card.scroll_into_view_if_needed()
            time.sleep(random.uniform(1.0, 2.0))

            paragrafos = card.locator("p")

            titulo = safe_text(paragrafos.nth(0).locator('span[aria-hidden="true"]').first)
            if titulo == "N/A":
                titulo = safe_text(paragrafos.nth(0))

            if not titulo_relevante(titulo):
                continue

            # Simula leitura/clique humano antes de abrir os detalhes da vaga
            time.sleep(random.uniform(0.8, 1.6))
            card.click()
            time.sleep(random.uniform(2.0, 3.5))

            box_descricao = page.locator(DESCRICAO_SELECTOR).first
            box_descricao.wait_for(state="visible", timeout=15000)

            descricao = box_descricao.inner_text() or ""
            # Simula tempo de leitura da descrição
            time.sleep(random.uniform(1.2, 2.5))

            if not descricao_relevante(descricao):
                print(f"Descrição rejeitada pelo filtro: {titulo}")
                continue

            component_key = card.get_attribute("componentkey") or ""
            vaga_id = component_key.replace("job-card-component-ref-", "").strip()

            empresa = safe_text(paragrafos.nth(1))
            localidade = safe_text(paragrafos.nth(2))

            data = safe_text(paragrafos.last.locator('span[aria-hidden="true"]'))
            if data == "N/A":
                data = "Promovida"

            link_vaga = f"https://www.linkedin.com/jobs/view/{vaga_id}/" if vaga_id else None

            if not vaga_id or not link_vaga:
                print(f"Card {i} ignorado: ID ou link ausente.")
                continue

            skills_match = calcular_aderencia_stack(titulo, descricao)
            linha_stack = f"🛠 <b>Stack:</b> {', '.join(skills_match)}\n" if skills_match else ""

            mensagem = (
                "🔥 <b>Nova vaga no LinkedIn!</b>\n\n"
                f"📌 <b>{titulo}</b>\n"
                f"🏢 {empresa}\n"
                f"📍 {localidade}\n"
                f"{linha_stack}"
                f"📅 {data}\n"
                f"🔗 {link_vaga}"
            )

            print(
                f"""
                Título: {titulo}
                Empresa: {empresa}
                Localidade: {localidade}
                Stack: {', '.join(skills_match) if skills_match else 'Geral Tech'}
                Data publicação: {data}
                Link: {link_vaga}
                Salvando vaga no banco... {vaga_id}
                """
            )

            salvar_vaga(
                vaga_id=vaga_id,
                fonte="LinkedIn",
                titulo=titulo,
                empresa=empresa,
                localidade=localidade,
                link_vaga=link_vaga,
                data_publicacao=data,
                mensagem=mensagem,
            )

        except Exception as e:
            print(f"Um erro inesperado aconteceu no card {i}: {e}")


def executar_linkedin_scraper(max_paginas: int = 4, headless: bool = False) -> None:
    origem_sessao = os.getenv("LINKEDIN_LOG")
    if not origem_sessao:
        for candidato in [RAIZ_PROJETO / "linkedin_log.json", BASE_DIR / "cookies" / "linkedin_log.json"]:
            if candidato.is_file():
                origem_sessao = str(candidato)
                break

    playwright, browser, context, page = iniciar_navegador(
        storage_state=origem_sessao,
        headless=headless,
    )

    try:
        page.set_default_timeout(60000)

        page.goto("https://www.linkedin.com/feed?nis=true", wait_until="domcontentloaded")
        time.sleep(random.uniform(5.0, 8.0))

        page.goto(
            "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4433197676"
            "&distance=25&f_E=1%2C2%2C3&f_F=it&f_I=96%2C4%2C6%2C3231&f_JT=F%2CP%2CC%2CI"
            "&f_TPR=r604800&f_WT=1%2C3%2C2&geoId=107636196&keywords=software"
            "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=DD",
            wait_until="domcontentloaded",
        )
        time.sleep(random.uniform(3.0, 5.0))

        pagina_atual = 1
        while pagina_atual <= max_paginas:
            print(f"\n=== Processando página {pagina_atual} de {max_paginas} ===")
            cards = scroll_current_page(page, max_scrolls=20)
            process_current_page(page, cards, max_vagas_pagina=50)

            if pagina_atual == max_paginas:
                print(f"Limite de {max_paginas} páginas atingido. Encerrando.")
                break

            next_button = page.locator(NEXT_BUTTON_SELECTOR)

            if next_button.count() == 0 or not next_button.is_enabled():
                print("Não há mais páginas. Encerrando.")
                break

            # Pausa maior antes e depois de avançar para a próxima página
            time.sleep(random.uniform(3.0, 5.5))
            next_button.scroll_into_view_if_needed()
            time.sleep(random.uniform(1.0, 2.0))
            next_button.click()
            time.sleep(random.uniform(4.5, 7.5))
            pagina_atual += 1

        time.sleep(random.uniform(3.0, 5.0))

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    executar_linkedin_scraper(max_paginas=4, headless=True)