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

BASE_URL = "https://santander.wd3.myworkdayjobs.com"
SEARCH_URL = (
    "https://santander.wd3.myworkdayjobs.com/pt-BR/SantanderCareers"
    "?locationCountry=1a29bb1357b240ab99a2fa755cc87c0e"
    "&jobFamilyGroup=047662461dfb01bf0a10a10a1a01d241"
    "&jobFamilyGroup=135a3ebce3810166e65b0db919012550"
    "&jobFamilyGroup=ab9adf92110e011571e710ab1a01034a"
    "&jobFamilyGroup=135a3ebce38101c45b3e18b919012750"
    "&jobFamilyGroup=135a3ebce38101db91d599b919013150"
    "&jobFamilyGroup=6cefe723149d01df0493a3f619014d4b"
)
NEXT_BUTTON_SELECTOR = 'nav[aria-label="pagination"] button[data-uxi-element-id="next"]'


def executar_santander_scraper(
    max_paginas: int = 5,
    max_vagas_pagina: int = 50,
    headless: bool = True,
) -> None:
    fonte = "Santander"
    playwright, browser, context, page = iniciar_navegador(headless=headless)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded")

        # Fecha eventual banner de cookies do Workday se aparecer
        try:
            btn_cookies = page.locator(
                'button[data-automation-id="legalNoticeAcceptButton"], button:has-text("Aceitar")'
            ).first
            if btn_cookies.is_visible(timeout=3000):
                btn_cookies.click()
        except Exception:
            pass

        pagina_atual = 1

        while pagina_atual <= max_paginas:
            print(f"\n=== Santander: Processando página {pagina_atual} ===")

            try:
                cards = rolar_ate_estabilizar(
                    page,
                    ".css-1q2dra3",
                    max_scrolls=25,
                    timeout_inicial=30000,
                )
            except PlaywrightTimeoutError:
                print("-> Nenhuma vaga encontrada no Santander para os filtros atuais.")
                break

            total_cards = min(cards.count(), max_vagas_pagina)
            print(f"-> {total_cards} vagas encontradas na página {pagina_atual}")

            primeiro_href_atual = (
                cards.first.locator('[data-automation-id="jobTitle"]').get_attribute("href")
            )

            for i in range(total_cards):
                try:
                    card = cards.nth(i)

                    titulo = safe_text(card.locator('[data-automation-id="jobTitle"]'))
                    if not titulo_relevante(titulo, exigir_nivel_no_titulo=True):
                        print(f"Título rejeitado pelo filtro: {titulo}")
                        continue

                    vaga_id = safe_text(card.locator('[data-automation-id="subtitle"] li'))
                    empresa = "Santander"
                    localidade = safe_text(card.locator('[data-automation-id="locations"] dd'))
                    href = card.locator('[data-automation-id="jobTitle"]').get_attribute("href")
                    link_vaga = urljoin(BASE_URL, href) if href else None
                    data = safe_text(card.locator('[data-automation-id="postedOn"] dd'))

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
                        "🔥 <b>Nova vaga no Santander!</b>\n\n"
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
                print("Não há mais páginas no Santander. Encerrando.")
                break

            next_button.scroll_into_view_if_needed()
            time.sleep(random.uniform(1.0, 2.0))
            next_button.click()

            # Aguarda o primeiro card do Workday atualizar antes de ler a próxima página
            if primeiro_href_atual:
                try:
                    page.wait_for_function(
                        """(hrefAntigo) => {
                            const el = document.querySelector('[data-automation-id="jobTitle"]');
                            return el && el.getAttribute('href') !== hrefAntigo;
                        }""",
                        arg=primeiro_href_atual,
                        timeout=15000,
                    )
                except PlaywrightTimeoutError:
                    pass

            time.sleep(random.uniform(1.5, 3.0))
            pagina_atual += 1

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    executar_santander_scraper(max_paginas=5, headless=True)