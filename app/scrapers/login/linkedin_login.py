from pathlib import Path

from playwright.sync_api import sync_playwright


ARQUIVO_SESSAO = Path(__file__).resolve().parents[3] / "linkedin_log.json"


with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()

    page.goto(
        "https://www.linkedin.com/login"
    )

    print("Faça login manualmente no LinkedIn")
    input("Depois do login pressione ENTER...")

    cookies = context.cookies("https://www.linkedin.com")
    if not any(cookie.get("name") == "li_at" for cookie in cookies):
        browser.close()
        raise RuntimeError(
            "Cookie de autenticação li_at não encontrado. Conclua o login "
            "no navegador e execute o script novamente."
        )

    context.storage_state(path=str(ARQUIVO_SESSAO))

    browser.close()

    print(f"Estado de sessão salvo em: {ARQUIVO_SESSAO}")
    print("Não compartilhe esse arquivo nem o envie ao repositório.")
