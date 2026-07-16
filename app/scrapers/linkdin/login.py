from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True, #True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google ebra ou não!
        args=[
            "--no-sandbox"
        ]
    )

    context = browser.new_context()

    page = context.new_page()

    page.goto(
        "https://www.linkedin.com/login"
    )

    print("Faça login manualmente no LinkedIn")
    input("Depois do login pressione ENTER...")

    context.storage_state(
        path="linkedin_log.json"
    )

    browser.close()

    print("Cookies salvos!")