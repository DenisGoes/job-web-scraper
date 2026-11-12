import json
import base64
import os
import random
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Locator, Page, Playwright, sync_playwright

load_dotenv()


def carregar_storage_state(origem):
    if not origem:
        return None
    if isinstance(origem, dict):
        return origem

    valor = str(origem).strip()
    if not valor:
        return None

    # 1. Se for um caminho de arquivo existente no disco (ex.: GitHub Actions / local)
    if os.path.exists(valor):
        with open(valor, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Se for string Base64 (ex.: variável de ambiente no Render)
    if not valor.startswith("{"):
        valor = base64.b64decode(valor).decode("utf-8")

    # 3. Faz o parse do JSON já decodificado
    return json.loads(valor)


def iniciar_navegador(
    storage_state: str | dict[str, Any] | None = None,
    headless: bool = True,
) -> tuple[Playwright, Browser, BrowserContext, Page]:
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=headless,
        args=["--no-sandbox"],
    )

    estado_resolvido = carregar_storage_state(storage_state)
    context = browser.new_context(storage_state=estado_resolvido)
    page = context.new_page()
    page.set_default_timeout(30000)

    return playwright, browser, context, page


def rolar_ate_estabilizar(
    page: Page,
    card_selector: str,
    max_scrolls: int = 15,
    timeout_inicial: int = 30000,
) -> Locator:
    page.wait_for_selector(card_selector, timeout=timeout_inicial)
    cards = page.locator(card_selector)
    cards.first.hover()

    vagas_antes = 0
    tentativas = 0

    while tentativas < max_scrolls:
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(int(random.uniform(700, 1300)))

        vagas_agora = cards.count()
        if vagas_agora == vagas_antes:
            break

        vagas_antes = vagas_agora
        tentativas += 1

    print(f"Scroll finalizado: {vagas_antes} vagas carregadas na tela.")
    return cards


def fechar_navegador(
    playwright: Playwright | None = None,
    browser: Browser | None = None,
    context: BrowserContext | None = None,
) -> None:
    if context:
        context.close()

    if browser:
        browser.close()

    if playwright:
        playwright.stop()