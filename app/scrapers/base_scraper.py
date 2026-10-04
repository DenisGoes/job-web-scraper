from playwright.sync_api import sync_playwright

from app.model.vaga import Vaga
from app.repository.vaga_repository import VagaRepository


class BaseScraper:

    def __init__(self, fonte):
        self.fonte = fonte
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.repository = VagaRepository()

    def iniciar_navegador(self, storage_state=None):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False, #True para produção, False para desenvolvimento - Esse trecho faz com que a janela do google ebra ou não!
            args=["--no-sandbox"]
        )

        self.context = self.browser.new_context(
            storage_state=storage_state
        )

        self.page = self.context.new_page()

        self.page.set_default_timeout(30000)

    def fechar_navegador(self):

        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()

    def salvar_vaga(self, vaga: Vaga):
        return self.repository.salvar(vaga)