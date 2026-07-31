from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True, #True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google abra ou não!
        args=[
            "--no-sandbox"
            # "--start-maximized" # Usado em desenvolvimento
        ]
    )

    context = browser.new_context()

    page = context.new_page()

    page.goto("https://www.infojobs.com.br/")

    print("Faça login manualmente no Infojobs")# Usado para debug
    input("Depois do login pressione ENTER...")# Usado para debug

    context.storage_state(
        path="infojobs_log.json"
    )

    browser.close()

    print("Cookies salvos!")# Usado para debug
    