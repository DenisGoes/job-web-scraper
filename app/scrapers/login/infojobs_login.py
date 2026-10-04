from playwright.sync_api import sync_playwright


def salvar_login_infojobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True #True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google ebra ou não!
        )

        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.infojobs.com.br/")

        print("Faça login manualmente no InfoJobs.")
        input("Depois que terminar o login, pressione ENTER aqui...")

        context.storage_state(path="infojobs.json")

        print("Login salvo em cookies/infojobs.json")

        browser.close()


if __name__ == "__main__":
    salvar_login_infojobs()