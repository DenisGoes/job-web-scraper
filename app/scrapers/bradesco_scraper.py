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

NEXT_BUTTON_SELECTOR = 'nav[data-tag="search-results-pagination"] button.next'


def executar_bradesco_scraper(
    max_paginas: int = 5,
    max_vagas_pagina: int = 50,
    headless: bool = True,
) -> None:
    fonte = "Bradesco"
    playwright, browser, context, page = iniciar_navegador(headless=headless)

    try:
        page.goto(
            "https://bradesco.csod.com/ux/ats/careersite/1/home?c=bradesco&cfdd[0][id]=634&cfdd[0][options][0]=1429&lq=Osasco%2C%20SP%2C%20Brasil&pl=ChIJB_KeWwj_zpQRTkyCTH3iIQ8&country=br&state=sp&city=osasco_barueri_sao%20paulo",
            wait_until="networkidle",
        )

        # Fecha eventual banner de cookies se aparecer
        try:
            btn_cookies = page.locator("button:has-text('Aceitar'), button:has-text('Accept')").first
            if btn_cookies.is_visible(timeout=3000):
                btn_cookies.click()
        except Exception:
            pass

        pagina_atual = 1

        while pagina_atual <= max_paginas:
            print(f"\n=== Bradesco: Processando página {pagina_atual} ===")

            try:
                titulos = rolar_ate_estabilizar(
                    page,
                    '[data-tag="displayJobTitle"]',
                    max_scrolls=25,
                    timeout_inicial=30000,
                )
            except PlaywrightTimeoutError:
                print("-> Nenhuma vaga encontrada no Bradesco para os filtros atuais.")
                break

            total_cards = min(titulos.count(), max_vagas_pagina)
            print(f"-> {total_cards} vagas encontradas na página {pagina_atual}")

            for i in range(total_cards):
                try:
                    titulo_el = titulos.nth(i)
                    card = titulo_el.locator(
                        "xpath=ancestor::div[contains(@class, 'p-panel')][1]"
                    )

                    titulo = safe_text(titulo_el)
                    if not titulo_relevante(titulo, exigir_nivel_no_titulo=True):
                        print(f"Título rejeitado pelo filtro: {titulo}")
                        continue

                    vaga_id = titulo_el.locator("p").get_attribute("data-tag")
                    empresa = "Bradesco"
                    localidade = safe_text(card.locator('[data-tag="displayJobLocation"]'))
                    href = titulo_el.get_attribute("href")
                    link_vaga = urljoin(page.url, href) if href else None
                    data = safe_text(card.locator('[data-tag="displayJobPostingDate"]'))

                    if not vaga_id or not link_vaga:
                        print(f"Vaga {i} ignorada: ID ou link ausente.")
                        continue

                    skills_match = calcular_aderencia_stack(titulo)
                    linha_stack = f"🛠 <b>Stack:</b> {', '.join(skills_match)}\n" if skills_match else ""

                    mensagem = (
                        "🔥 <b>Nova vaga no Bradesco!</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"🏢 {empresa}\n"
                        f"📍 {localidade}\n"
                        f"{linha_stack}"
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

                    salvar_vaga(
                        vaga_id=vaga_id,
                        fonte=fonte,
                        titulo=titulo,
                        empresa=empresa,
                        localidade=localidade,
                        link_vaga=link_vaga,
                        data_publicacao=data,
                        mensagem=mensagem,
                    )

                except Exception as e:
                    print(f"Erro ao processar vaga {i}: {e}")

            if pagina_atual == max_paginas:
                print(f"Limite de {max_paginas} páginas atingido. Encerrando.")
                break

            next_button = page.locator(NEXT_BUTTON_SELECTOR).first
            if next_button.count() == 0 or not next_button.is_enabled():
                print("Não há mais páginas no Bradesco. Encerrando.")
                break

            next_button.scroll_into_view_if_needed()
            time.sleep(random.uniform(1.0, 2.0))
            next_button.click()

            # Aguarda a troca dos cards na SPA antes de iniciar a próxima página
            time.sleep(random.uniform(3.0, 5.0))
            pagina_atual += 1

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    executar_bradesco_scraper(max_paginas=5, headless=True)