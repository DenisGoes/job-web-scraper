import json
from pathlib import Path

from playwright.sync_api import sync_playwright

# Salva na raiz do projeto (job-web-scraper/linkedin_log.json)
ARQUIVO_SESSAO = Path.cwd() / "linkedin_log.json"


def gerar_sessao_linkedin() -> None:
    with sync_playwright() as p:
        # Precisa ser False para a janela abrir e poder digitar o login
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.linkedin.com/login")

        print("Faça login manualmente no LinkedIn na janela que abriu.")
        input("Depois que o feed carregar, volte aqui e pressione ENTER...")

        cookies = context.cookies("https://www.linkedin.com")
        if not any(cookie.get("name") == "li_at" for cookie in cookies):
            browser.close()
            raise RuntimeError(
                "Cookie de autenticação li_at não encontrado. Conclua o login "
                "no navegador e execute o script novamente."
            )

        context.storage_state(path=str(ARQUIVO_SESSAO))
        browser.close()

        print(f"\nEstado de sessão salvo em: {ARQUIVO_SESSAO}")
        print("Não compartilhe esse arquivo nem o envie ao repositório.\n")

        sessao_compacta = json.dumps(json.loads(ARQUIVO_SESSAO.read_text(encoding="utf-8")))
        print("Para colar no seu .env:")
        print(f"LINKEDIN_LOG='{sessao_compacta}'")


if __name__ == "__main__":
    gerar_sessao_linkedin()