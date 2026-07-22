from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from app.database.crud.crud_linkedin import salvar_vaga
from app.scrapers.linkedin.filtros import (
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
        cards = page.locator("[data-job-id]")
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
        page.wait_for_selector("[data-job-id]", timeout=20000)
    except PlaywrightTimeoutError:
        print("Nenhum card de vaga carregou.")
        return
    time.sleep(3)

    cards = page.locator("[data-job-id]")
    total_cards = cards.count()
    print(f"  -> {total_cards} vagas encontradas nesta página")

    for i in range(total_cards):
        try:
            card = cards.nth(i)
            card.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.5, 1.0))
            titulo = safe_text(card.locator("a[data-control-id] strong"))

            if not titulo_relevante(titulo):
                continue

            card.click()
            page.locator("#job-details").wait_for()

            descricao = page.locator("#job-details .mt4").text_content()
            # print("=" * 50) #Usado para debug
            # print(descricao[:300])  # primeiros 300 caracteres #Usado para debug
            # print(descricao_relevante(descricao)) #Usado para debug

            if not descricao_relevante(descricao):
                continue

            vaga_id = card.get_attribute("data-job-id")
            empresa = safe_text(
                card.locator(".lhTrJwLJdNHzUTaZGzxGMSDIlaANTfgvhPQTuoU")
            )
            localidade = safe_text(card.locator("li span[dir='ltr']").first)
            data = safe_text(card.locator("time"))
            if data == "N/A":
                data = "Promovida"

            link_vaga = card.locator("a[data-control-id]").get_attribute("href")
            link_vaga = "https://www.linkedin.com" + link_vaga if link_vaga else "N/A"

            mensagem = (
                "🔥 <b>Nova vaga no LinkedIn!</b>\n\n"
                f"📌 <b>{titulo}</b>\n"
                f"🏢 {empresa}\n"
                f"📍 {localidade}\n"
                f"📅 {data}\n"
                f"🔗 {link_vaga}"
            )

            print(f"""
                Titulo: {titulo}
                Empresa: {empresa}
                Localidade: {localidade}
                Data publicação: {data}
                Link: {link_vaga}
                Salvando vaga no banco... {vaga_id}
            """)

            salvar_vaga(
                vaga_id=vaga_id,
                fonte="linkedin",
                titulo=titulo,
                empresa=empresa,
                localidade=localidade,
                link_vaga=link_vaga,
                data_publicacao=data,
                mensagem=mensagem,
            )

        except Exception as e:
            print(f"Um erro inesperado aconteceu no card {i}: {e}")


def run_scraper_linkdin(max_paginas=4):
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
            "https://www.linkedin.com/jobs/search/?currentJobId=4441999555&distance=10&f_E=1%2C2%2C3&f_JT=F%2CP%2CC%2CI%2CO&f_TPR=r604800&geoId=104746682&keywords=desenvolvedor&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R",
            wait_until="domcontentloaded",
        )

        pagina_atual = 1
        while pagina_atual <= max_paginas:
            print(f"\n=== Processando página {pagina_atual} ===")
            process_current_page(page)
            scroll_current_page(page)
            process_current_page(page)

            next_button = page.locator("button.jobs-search-pagination__button--next")

            if next_button.count() == 0 or not next_button.is_enabled():
                print("Não há mais páginas. Encerrando.")
                break

            next_button.click()

            page.wait_for_timeout(random.randint(4000, 6000))

            page.wait_for_selector("[data-job-id]")

            pagina_atual += 1

        time.sleep(3)
        browser.close()


# Todos os prints foram usados com o proposito de debug!!!
