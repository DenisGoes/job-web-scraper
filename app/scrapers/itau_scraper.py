import random
import time
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.database.repository import salvar_vaga
from app.scrapers.base_scraper import (
    fechar_navegador,
    iniciar_navegador,
    rolar_ate_estabilizar,
)
from app.scrapers.filtros import (
    calcular_aderencia_stack,
    safe_text,
    titulo_relevante,
)

BASE_URL = "https://carreiras.itau.com.br"
SEARCH_URL = (
    f"{BASE_URL}/busca-de-vagas?k=&ac=8274976&State=3469034-3448433&orgIds=35299"
)
NEXT_BUTTON_SELECTOR = "#pagination-bottom a.next"


def executar_itau_scraper(
    max_paginas: int = 5,
    max_vagas_pagina: int = 50,
    headless: bool = True,
) -> None:
    fonte = "Itaú"
    playwright, browser, context, page = iniciar_navegador(headless=headless)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded")

        # Fecha eventual banner de cookies se aparecer
        try:
            btn_cookies = page.locator(
                "button:has-text('Aceitar'), button:has-text('Concordar'), #gdpr-button"
            ).first
            if btn_cookies.is_visible(timeout=3000):
                btn_cookies.click()
        except Exception:
            pass

        pagina_atual = 1

        while pagina_atual <= max_paginas:
            print(f"\n=== Itaú: Processando página {pagina_atual} ===")

            try:
                cards = rolar_ate_estabilizar(
                    page,
                    ".results__item",
                    max_scrolls=25,
                    timeout_inicial=30000,
                )
            except PlaywrightTimeoutError:
                print("-> Nenhuma vaga encontrada no Itaú para os filtros atuais.")
                break

            total_cards = min(cards.count(), max_vagas_pagina)
            print(f"-> {total_cards} vagas encontradas na página {pagina_atual}")

            primeiro_id_atual = (
                cards.first.locator("a.results__item-link").get_attribute("data-job-id")
            )

            for i in range(total_cards):
                try:
                    card = cards.nth(i)

                    link_el = card.locator("a.results__item-link")
                    titulo = safe_text(link_el.locator("h2.results__item-heading"))
                    if not titulo_relevante(titulo, exigir_nivel_no_titulo=True):
                        print(f"Título rejeitado pelo filtro: {titulo}")
                        continue

                    vaga_id = link_el.get_attribute("data-job-id")
                    empresa = "Itaú"
                    localidade = safe_text(link_el.locator(".job-location"))
                    href = link_el.get_attribute("href")
                    link_vaga = urljoin(BASE_URL, href) if href else None

                    if not vaga_id or not link_vaga:
                        print(f"Vaga {i} ignorada: ID ou link ausente.")
                        continue

                    skills_match = calcular_aderencia_stack(titulo)
                    linha_stack = (
                        f"🛠 <b>Stack:</b> {', '.join(skills_match)}\n"
                        if skills_match
                        else ""
                    )

                    mensagem = (
                        "🔥 <b>Nova vaga no Itaú!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"{linha_stack}"
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

                    salvar_vaga(
                        vaga_id=vaga_id,
                        fonte=fonte,
                        titulo=titulo,
                        empresa=empresa,
                        localidade=localidade,
                        link_vaga=link_vaga,
                        mensagem=mensagem,
                    )

                except Exception as e:
                    print(f"Erro ao processar vaga {i}: {e}")

            if pagina_atual == max_paginas:
                print(f"Limite de {max_paginas} páginas atingido. Encerrando.")
                break

            next_button = page.locator(NEXT_BUTTON_SELECTOR).first
            classes_next = next_button.get_attribute("class") or "" if next_button.count() > 0 else "disabled"

            if next_button.count() == 0 or "disabled" in classes_next.split():
                print("Não há mais páginas no Itaú. Encerrando.")
                break

            next_button.scroll_into_view_if_needed()
            time.sleep(random.uniform(1.0, 2.0))
            next_button.click()

            # Aguarda o primeiro card mudar antes de avançar para a próxima página
            if primeiro_id_atual:
                try:
                    page.wait_for_function(
                        """(idAntigo) => {
                            const el = document.querySelector('.results__item a.results__item-link');
                            return el && el.getAttribute('data-job-id') !== idAntigo;
                        }""",
                        arg=primeiro_id_atual,
                        timeout=15000,
                    )
                except PlaywrightTimeoutError:
                    pass

            time.sleep(random.uniform(1.5, 3.0))
            pagina_atual += 1

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    executar_itau_scraper(max_paginas=5, headless=True)