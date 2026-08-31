from playwright.sync_api import sync_playwright
from backend.database.crud.crud_vaga import salvar_vaga
from backend.scrapers.filtros import safe_text
import time


def run_scraper_santander():

    # Inicia o navegador utilizando uma sessão persistente.
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google abra ou não!
            args=[
                "--no-sandbox"
                # "--start-maximized" # Usado em desenvolvimento
            ],
        )

        context = browser.new_context()

        page = context.new_page()
        page.set_default_timeout(30000)  # evita timeout de 30s padrão em ações lentas

        # Acessa a página de vagas já filtrada com as preferências desejadas.
        page.goto(
            "https://santander.wd3.myworkdayjobs.com/pt-BR/SantanderCareers?locationCountry=1a29bb1357b240ab99a2fa755cc87c0e&locationRegionStateProvince=6177762425c54ca8aa31aac74fb08fad&jobFamilyGroup=ab9adf92110e01018e26d3aa1a01014a&jobFamilyGroup=135a3ebce38101c45b3e18b919012750&jobFamilyGroup=6cefe723149d01b7cf3faef619014f4b&jobFamilyGroup=135a3ebce3810166e65b0db919012550&jobFamilyGroup=047662461dfb01bf0a10a10a1a01d241&jobFamilyGroup=135a3ebce38101db91d599b919013150&jobFamilyGroup=ab9adf92110e0160f08437aa1a01f549",
            wait_until="domcontentloaded",
        )
        page.wait_for_selector(
            ".css-1q2dra3", timeout=30000
        )  # Aguarda o carregamento dos cards de vagas.

        cards = page.locator(".css-1q2dra3")

        # Limita a quantidade de vagas processadas.
        total_cards = cards.count()
        print(f"  -> {total_cards} vagas encontradas nesta página")

        # Percorre cada vaga encontrada na página.
        for i in range(total_cards):
            try:
                card = cards.nth(i)
                # close_popups(page)
                titulo = safe_text(card.locator('[data-automation-id="jobTitle"]'))

                # Coleta todas as informações da vaga.
                vaga_id = safe_text(card.locator('[data-automation-id="subtitle"] li'))
                empresa = "Santander"
                localidade = safe_text(
                    card.locator('[data-automation-id="locations"] dd')
                )

                link_vaga = card.locator(
                    '[data-automation-id="jobTitle"]'
                ).get_attribute("href")
                data = safe_text(card.locator('[data-automation-id="postedOn"] dd'))

                mensagem = (
                    "🔥 <b>Nova vaga no Santander!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {empresa}\n"
                    f"📍 {localidade}\n"
                    f"📅 {data}\n"
                    f"🔗 {link_vaga}"
                )
                # Exibe os dados coletados no terminal.
                print(f"""
                    Titulo: {titulo}
                    Empresa: {empresa}
                    Localidade: {localidade}
                    Link: {link_vaga}
                    Data: {data}
                    Salvando vaga no banco... {vaga_id}
                    """)

                # Salva a vaga no banco de dados.
                salvar_vaga(
                    vaga_id=vaga_id,
                    fonte="santander",
                    titulo=titulo,
                    empresa=empresa,
                    localidade=localidade,
                    link_vaga=link_vaga,
                    data_publicacao=data,
                    mensagem=mensagem,
                )

            except Exception as e:
                # Continua processando as demais vagas caso ocorra um erro.
                print(f"Um erro inesperado aconteceu! {e}")

        time.sleep(3)

        # Encerra o navegador.
        browser.close()
