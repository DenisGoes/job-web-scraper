from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from backend.database.crud.crud_linkedin import salvar_vaga
from backend.scrapers.fontes.linkedin.filtros import (
    safe_text,
    titulo_relevante,
    descricao_relevante,
)
import time, random, os, json

# Define o diretório onde os cookies da sessão serão armazenados.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, "cookies")
os.makedirs(COOKIES_PATH, exist_ok=True)


# Rola a lista de vagas da página atual algumas vezes,
# só para garantir que os cards visíveis carreguem imagens/lazy content.
def scroll_current_page(page, times=5):
    print("Executando scroll...")

    try:
        cards = page.locator('div[role="button"][componentkey^="job-card-component-ref-"]')
        quantidade = cards.count()
        print(f"Cards encontrados antes do scroll: {quantidade}")

        if quantidade > 0:
            try:
                cards.first.hover(timeout=5000)
            except Exception:
                print("Não foi possível fazer hover no card. Continuando scroll.")
        else:
            print("Nenhum card encontrado. Fazendo scroll normal.")

        for _ in range(times):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(int(random.uniform(800, 1500)))

    except Exception as e:
        print(f"Erro no scroll: {e}")


# Processa todos os cards de vaga carregados na página atual.
def process_current_page(page):
    try:
        page.wait_for_selector('button[data-testid="pagination-controls-next-button-visible"]', timeout=20000)
    except PlaywrightTimeoutError:
        print("Nenhum card de vaga carregou.")
        return
    time.sleep(3)

    cards = page.locator('div[role="button"][componentkey^="job-card-component-ref-"]')
    total_cards = cards.count()
    print(f"  -> {total_cards} vagas encontradas nesta página")

    for i in range(total_cards):
        try:
            card = cards.nth(i)

            componentkey = card.get_attribute("componentkey")

            if not componentkey:
                print(f"Card {i} não possui componentkey.")
                continue

            vaga_id = componentkey.replace("job-card-component-ref-", "",)

            card.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.5, 1.0))
            titulo = safe_text(card.locator("span[aria-hidden='true']").first)

            if not titulo_relevante(titulo):
                continue

            link_vaga = (f"https://www.linkedin.com/jobs/view/{vaga_id}/")

            mensagem = (
                "🔥 <b>Nova vaga no LinkedIn!</b>\n\n"
                f"📌 <b>{titulo}</b>\n"
                f"🔗 {link_vaga}"
            )

            print(f"""
                Titulo: {titulo}
                Link: {link_vaga}
                Salvando vaga no banco... {vaga_id}
            """)

            salvar_vaga(
                vaga_id=vaga_id,
                fonte="linkedin",
                titulo=titulo,
                link_vaga=link_vaga,
                mensagem=mensagem,
            )

        except Exception as e:
            print(f"Um erro inesperado aconteceu no card {i}: {e}")


def run_scraper_linkdin(max_paginas=1):
    LINKEDIN_LOG = os.getenv("LINKEDIN_LOG")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google ebra ou não!
            args=[
                "--no-sandbox"
                # "--start-maximized" # Usado em desenvolvimento
            ],
        )

        # Verificando credenciais e criando um contexto.
        if LINKEDIN_LOG:
            context = browser.new_context(
                storage_state=json.loads(
                    LINKEDIN_LOG
                )  # Variavel de ambiente usada em produção!
            )
        else:
            STATE_PATH = os.path.join(  # Caminho absoluto usado em desenvolvimento!
                BASE_DIR, "cookies", "linkedin_log.json"
            )

            context = browser.new_context(storage_state=STATE_PATH)

        page = context.new_page()
        page.set_default_timeout(30000)  # evita timeout de 30s padrão em ações lentas

        page.goto(
            "https://www.linkedin.com/feed?nis=true", wait_until="domcontentloaded"
        )
        time.sleep(
            15
        )  # Time de 15 segundos, devido a nova atualização do linkedin, que ficou mais lento.

        # Acessa a página de vagas já filtrada com as preferências desejadas.
        page.goto(
            "https://www.linkedin.com/jobs/search/?currentJobId=4448035104&distance=25&f_E=1%2C2%2C3&f_JT=F%2CP%2CC%2CI%2CO&f_TPR=r604800&f_WT=2%2C1%2C3&geoId=104746682&keywords=desenvolvedor&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R",
            wait_until="domcontentloaded",
        )

        pagina_atual = 1
        while pagina_atual <= max_paginas:
            print(f"\n=== Processando página {pagina_atual} ===")
            process_current_page(page)
            scroll_current_page(page)
            process_current_page(page)

            next_button = page.locator("button.pagination-controls-next-button-visible")

            if next_button.count() == 0 or not next_button.is_enabled():
                print("Não há mais páginas. Encerrando.")
                break

            next_button.click()

            page.wait_for_timeout(random.randint(4000, 6000))

            page.wait_for_selector('div[role="button"][componentkey^="job-card-component-ref-"]')

            pagina_atual += 1

        time.sleep(3)
        browser.close()


# Todos os prints foram usados com o proposito de debug!!!