from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from backend.database.crud.crud_linkedin import salvar_vaga, get_ids_existentes
from backend.scrapers.filtros import (
    safe_text,
    titulo_relevante,
    descricao_relevante,
)
import time, random, os, json, re

# Define o diretório onde os cookies da sessão serão armazenados.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, "cookies")
os.makedirs(COOKIES_PATH, exist_ok=True)

SEARCH_URL_BASE = (
    "https://www.linkedin.com/jobs/search/"
    "?distance=25&f_E=1%2C2%2C3&f_JT=F%2CP%2CC%2CI%2CO&f_TPR=r604800"
    "&f_WT=2%2C1%2C3&geoId=104746682&keywords=desenvolvedor"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=R"
)

VAGAS_POR_PAGINA = 25  # padrão do LinkedIn
JOB_LINK_SELECTOR = 'a[href*="/jobs/view/"]'
ID_MINIMO_DIGITOS = 8


def extrair_vaga_id(href):
    match = re.search(r"/jobs/view/(?:.*-)?(\d{" + str(ID_MINIMO_DIGITOS) + r",})", href)
    return match.group(1) if match else None

def limpar_titulo(texto):
    if not texto:
        return ""

    texto = re.sub(r"\s*with verification\s*$", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto).strip()

    metade = len(texto) // 2
    if metade > 0:
        parte1, parte2 = texto[:metade].strip(), texto[metade:].strip()
        if parte1 and parte1 == parte2:
            texto = parte1

    return texto.strip()

def scroll_current_page(page, times=5):
    print("Executando scroll...")

    try:
        links = page.locator(JOB_LINK_SELECTOR)
        quantidade = links.count()
        print(f"Links de vaga encontrados antes do scroll: {quantidade}")

        if quantidade > 0:
            try:
                links.first.hover(timeout=5000)
            except Exception:
                print("Não foi possível fazer hover no primeiro link. Continuando scroll.")
        else:
            print("Nenhum link de vaga encontrado. Fazendo scroll normal.")

        for _ in range(times):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(int(random.uniform(800, 1500)))

    except Exception as e:
        print(f"Erro no scroll: {e}")

def extrair_descricao(page, timeout=10000):
    descricao = ""
    try:
        painel = page.locator("div#job-details")
        painel.wait_for(state="visible", timeout=timeout)
        descricao = safe_text(painel)
    except PlaywrightTimeoutError:
        print("Painel de descrição não carregou a tempo.")
    except Exception as e:
        print(f"Erro ao extrair descrição: {e}")

    return descricao


def process_current_page(page, vagas_conhecidas):
    try:
        page.wait_for_selector(JOB_LINK_SELECTOR, timeout=20000)
    except PlaywrightTimeoutError:
        print("Nenhuma vaga carregou nesta página.")
        return 0

    time.sleep(3)

    links = page.locator(JOB_LINK_SELECTOR)
    total_links = links.count()
    print(f"  -> {total_links} links de vaga encontrados nesta página (bruto, com duplicatas)")

    vagas_ja_vistas = set()
    processadas = 0

    for i in range(total_links):
        try:
            link = links.nth(i)
            href = link.get_attribute("href")

            if not href:
                continue

            vaga_id = extrair_vaga_id(href)

            if not vaga_id or vaga_id in vagas_ja_vistas:
                continue  # LinkedIn repete o mesmo link em vários elementos do card

            vagas_ja_vistas.add(vaga_id)

            # Pula vagas que já existem no banco, antes de gastar tempo com
            # scroll/click/extração de descrição.
            if vaga_id in vagas_conhecidas:
                continue

            link.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.5, 1.0))

            titulo = safe_text(link)
            if not titulo:
                # fallback: alguns links não têm texto direto, o título
                # fica num span[aria-hidden] dentro/perto do link
                titulo = safe_text(link.locator("span[aria-hidden='true']").first)

            titulo = limpar_titulo(titulo)

            if not titulo_relevante(titulo):
                continue

            link_vaga = f"https://www.linkedin.com/jobs/view/{vaga_id}/"

            # Clica no link para abrir o painel de detalhes e ler a descrição.
            descricao = ""
            try:
                link.click()
                page.wait_for_timeout(int(random.uniform(1200, 2000)))
                descricao = extrair_descricao(page)
            except Exception as e:
                print(f"Não foi possível abrir/ler descrição da vaga {vaga_id}: {e}")

            if descricao and not descricao_relevante(descricao):
                continue

            mensagem = (
                "🔥 <b>Nova vaga no LinkedIn!</b>\n\n"
                f"📌 <b>{titulo}</b>\n"
                f"🔗 {link_vaga}"
            )

            print(f"""
                Titulo: {titulo}
                Link: {link_vaga}
                Descrição (preview): {descricao[:150]}
                Salvando vaga no banco... {vaga_id}
            """)

            salvo = salvar_vaga(
                vaga_id=vaga_id,
                fonte="linkedin",
                titulo=titulo,
                link_vaga=link_vaga,
                mensagem=mensagem,
                descricao=descricao,
            )

            if salvo:
                # Evita reprocessar/tentar salvar de novo se o mesmo card
                # aparecer em outra página durante essa mesma execução.
                vagas_conhecidas.add(vaga_id)
                processadas += 1

        except Exception as e:
            print(f"Um erro inesperado aconteceu no link {i}: {e}")

    return processadas


def run_scraper_linkdin(max_paginas=1):
    LINKEDIN_LOG = os.getenv("LINKEDIN_LOG")

    # Carrega uma única vez todos os IDs já salvos no banco, evitando
    # uma query por vaga durante o loop de processamento.
    vagas_conhecidas = get_ids_existentes(fonte="linkedin")
    print(f"{len(vagas_conhecidas)} vaga(s) já existentes no banco (serão puladas).")

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
                )  # Variável de ambiente usada em produção!
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
        )  # 15s devido à atualização do LinkedIn, que ficou mais lento.

        pagina_atual = 1
        while pagina_atual <= max_paginas:
            start = (pagina_atual - 1) * VAGAS_POR_PAGINA
            url_pagina = f"{SEARCH_URL_BASE}&start={start}"

            print(f"\n=== Processando página {pagina_atual} (start={start}) ===")
            page.goto(url_pagina, wait_until="domcontentloaded")
            time.sleep(5)  # dá tempo da página renderizar antes de checar seletor

            scroll_current_page(page)
            processadas = process_current_page(page, vagas_conhecidas)

            if processadas == 0:
                print("Nenhuma vaga processada nesta página. Encerrando.")
                break

            pagina_atual += 1

        time.sleep(3)
        browser.close()