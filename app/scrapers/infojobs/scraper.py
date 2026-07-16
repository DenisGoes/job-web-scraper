from playwright.sync_api import sync_playwright
from app.database.crud.crud_infojobs import salvar_vaga
from app.scrapers.infojobs.filtros import safe_text, titulo_relevante, descricao_relevante
import time, random, os, json

# Define o diretório onde os cookies da sessão serão armazenados.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, "cookies")
os.makedirs(COOKIES_PATH, exist_ok=True)


def close_popups(page):
    try:
        modal = page.locator("#modalPremiumDestaque")

        if modal.is_visible():
            print("Fechando popup premium...")

            close_button = page.locator(
                "#modalPremiumDestaque button"
            )

            if close_button.count() > 0:
                close_button.first.click()
            else:
                page.keyboard.press("Escape")

            page.wait_for_timeout(1000)

    except Exception:
        pass

def run_scraper_infojobs():
    
    INFOJOBS_LOG = os.getenv("INFOJOBS_LOG")
    # Inicia o navegador utilizando uma sessão persistente.
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, #True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google ebra ou não!
            args=["--no-sandbox", "--start-maximized"]
        )

        if INFOJOBS_LOG:
            context = browser.new_context(
                storage_state=json.loads(INFOJOBS_LOG) #Variavel de ambiente usada em produção!
            )
        else:
            STATE_PATH = os.path.join( #Caminho absoluto usado em desenvolvimento!
                BASE_DIR,
                "cookies",
                "infojobslog.json"
            )

            context = browser.new_context(
                storage_state=STATE_PATH
            )

        page = context.new_page()

        # Acessa o InfoJobs para carregar a sessão salva.
        page.goto("https://www.infojobs.com.br/", wait_until="domcontentloaded")
        time.sleep(5)

        # Acessa a página de vagas já filtrada com as preferências desejadas.
        page.goto(
            "https://www.infojobs.com.br/vagas-de-emprego-desenvolvimento+de+software-em-sao-paulo,-sp.aspx?categoria=74&sprd=25&splat=-23.48922&splng=-46.8059&tipocontrato=2,4,15&wo=1,2,5&im=1,4,5,6",
            wait_until="domcontentloaded"
        )

        # Aguarda o carregamento dos cards de vagas.
        page.wait_for_selector(".js_vacancyLoad", timeout=20000)
        time.sleep(3)

        cards = page.locator(".js_vacancyLoad")

        # Limita a quantidade de vagas processadas.
        max_vagas = 25
        total_cards = min(cards.count(), max_vagas)
        print(f"  -> {total_cards} vagas encontradas nesta página")

        # Percorre cada vaga encontrada na página.
        for i in range(total_cards):
            try:
                card = cards.nth(i)
                close_popups(page)
                titulo = safe_text(card.locator(".js_vacancyTitle"))
                if not titulo_relevante(titulo):
                    continue

                # Evita bloqueio do popup
                card.evaluate("(element) => element.click()")
                page.wait_for_timeout(2000)
                close_popups(page)
                
                descricao_locator = page.locator("div.text-medium").first
                descricao_locator.wait_for(state="visible", timeout=10000)

                descricao = descricao_locator.text_content()

                #Prints usados para debug no terminal
                # print("=" * 50)
                # print(descricao[:300])  # primeiros 300 caracteres
                # print(descricao_relevante(descricao))

                if not descricao_relevante(descricao):
                    continue

                # Coleta todas as informações da vaga.
                vaga_id = card.get_attribute("data-id")
                empresa = safe_text(card.locator("div.text-body a"))
                localidade = safe_text(card.locator(".mb-8").first)
                salario = safe_text(card.locator(".icon-money").locator("xpath=.."))
                modelo_trabalho = safe_text(card.locator(".icon-buildings").locator("xpath=.."))
                link_vaga = card.locator("a:has(h2.js_vacancyTitle)").evaluate("el => el.href")
                data = safe_text(card.locator(".small.text-nowrap"))

                mensagem = (
                    "🔥 <b>Nova vaga no InfoJobs!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {empresa}\n"
                    f"📍 {localidade}\n"
                    f"{salario}\n"
                    f"{modelo_trabalho}\n"
                    f"📅 {data}\n"
                    f"🔗 {link_vaga}"
                )
                # Exibe os dados coletados no terminal.
                print(f"""
                    Titulo: {titulo}
                    Empresa: {empresa}
                    Localidade: {localidade}
                    Salário: {salario}
                    Modelo de trabalho: {modelo_trabalho}
                    Link: {link_vaga}
                    Data: {data}
                    Salvando vaga no banco... {vaga_id}
                    """)

                # Salva a vaga no banco de dados.
                salvar_vaga(
                    vaga_id=vaga_id,
                    fonte="infojobs",
                    titulo=titulo,
                    empresa=empresa,
                    localidade=localidade,
                    salario=salario,
                    modelo_trabalho=modelo_trabalho,
                    link_vaga=link_vaga,
                    data_publicacao=data,
                    mensagem=mensagem,
                )

            except Exception as e:
                # Continua processando as demais vagas caso ocorra um erro.
                print(f"Um erro inesperado aconteceu! {e}")

        time.sleep(5)

        # Encerra o navegador.
        browser.close()