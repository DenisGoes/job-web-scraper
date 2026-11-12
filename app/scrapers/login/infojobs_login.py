from pathlib import Path

from app.scrapers.base_scraper import fechar_navegador, iniciar_navegador

RAIZ_PROJETO = Path.cwd()
CAMINHO_SAIDA = RAIZ_PROJETO / "infojobslog.json"


def salvar_login_infojobs(caminho_arquivo: Path = CAMINHO_SAIDA) -> None:
    playwright, browser, context, page = iniciar_navegador(headless=False)

    try:
        page.goto("https://www.infojobs.com.br/", wait_until="domcontentloaded")

        print("\n=== Captura de Sessão - InfoJobs ===")
        print("1. Faça login manualmente na janela do navegador que foi aberta.")
        print("2. Resolva qualquer captcha ou confirmação de e-mail/SMS, se aparecer.")
        input("3. Depois que estiver logado na sua conta, pressione ENTER aqui...")

        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(caminho_arquivo))

        print(f"\nLogin salvo com sucesso em: {caminho_arquivo}")
        print("Dica: para produção, você pode copiar o conteúdo desse JSON para a variável INFOJOBS_LOG no .env.")

    finally:
        fechar_navegador(playwright, browser, context)


if __name__ == "__main__":
    salvar_login_infojobs()