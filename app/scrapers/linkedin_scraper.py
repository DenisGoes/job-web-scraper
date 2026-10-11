import json
import re
from html import escape
from pathlib import Path

from app.config.settings import LINKEDIN_LOG
from app.model.vaga import Vaga
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.filtros import descricao_relevante, titulo_relevante


BASE_DIR = Path(__file__).resolve().parent
MAX_VAGAS_POR_PAGINA = 25
MAX_PAGINAS = 3
URL_BUSCA = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=estagi%C3%A1rio%20desenvolvimento%20software"
    "&location=Osasco%2C%20S%C3%A3o%20Paulo%2C%20Brasil"
    "&f_WT=1%2C2%2C3"
)


class LinkedinScraper(BaseScraper):
    """Scraper da listagem de vagas do LinkedIn autenticada por storage state."""

    def _storage_state(self):
        if LINKEDIN_LOG:
            try:
                return json.loads(LINKEDIN_LOG)
            except (json.JSONDecodeError, TypeError):
                return LINKEDIN_LOG

        opcoes = [
            BASE_DIR / "cookies" / "linkedin_log.json",
            BASE_DIR.parent.parent / "linkedin_log.json",
        ]
        for caminho in opcoes:
            if caminho.exists():
                return str(caminho)

        raise FileNotFoundError(
            "Sessão do LinkedIn não encontrada. Configure LINKEDIN_LOG "
            "ou salve linkedin_log.json na raiz do projeto."
        )

    @staticmethod
    def _texto(locator, padrao=""):
        try:
            if locator.count() > 0:
                return locator.first.inner_text().strip()
        except Exception:
            pass
        return padrao

    @staticmethod
    def _id_vaga(card):
        component_key = card.get_attribute("componentkey") or ""
        match = re.search(r"job-card-component-ref-(\d+)", component_key)
        if match:
            return match.group(1)

        links = card.locator("a[href*='currentJobId=']")
        href = links.first.get_attribute("href") if links.count() else None
        match = re.search(r"currentJobId=(\d+)", href or "")
        return match.group(1) if match else None

    def _descricao(self, titulo):
        seletores = (
            "[data-testid*='job-description']",
            "[data-test-id*='job-description']",
            "[componentkey*='job-description']",
            ".jobs-description__content",
            ".jobs-search__job-details--container",
            "#job-details",
        )

        for seletor in seletores:
            candidatos = self.page.locator(seletor)
            for indice in range(min(candidatos.count(), 3)):
                texto = self._texto(candidatos.nth(indice))
                if len(texto) > 100 and titulo.casefold() in texto.casefold():
                    return texto[:12000]

        # No layout novo do LinkedIn, o detalhe pode aparecer em outra coluna lazy.
        colunas = self.page.locator("[data-testid='lazy-column']")
        for indice in range(colunas.count()):
            coluna = colunas.nth(indice)
            chave = coluna.get_attribute("componentkey") or ""
            texto = self._texto(coluna)
            if (
                chave != "SearchResultsMainContent"
                and len(texto) > 100
                and titulo.casefold() in texto.casefold()
            ):
                return texto[:12000]

        return "Descrição completa não carregada pelo LinkedIn. Consulte a vaga no link."

    def _processar_card(self, card):
        vaga_id = self._id_vaga(card)
        if not vaga_id:
            print("Card do LinkedIn sem ID; ignorando.")
            return

        paragrafos = card.locator("p")
        if not paragrafos.count():
            print(f"Card {vaga_id} sem título nem dados textuais; ignorando.")
            return

        titulo = self._texto(
            paragrafos.nth(0).locator("span:not([aria-hidden='true'])")
        ) or self._texto(paragrafos.nth(0))
        empresa = self._texto(paragrafos.nth(1), "Empresa não informada")
        localidade = self._texto(paragrafos.nth(2), "Localidade não informada")

        # O cartão novo usa classes geradas; o componentkey contém o ID estável.
        link_vaga = f"https://www.linkedin.com/jobs/view/{vaga_id}/"

        if not titulo or not titulo_relevante(titulo):
            return

        try:
            card.scroll_into_view_if_needed()
            card.click()
            self.page.wait_for_timeout(1200)
        except Exception as erro:
            print(f"Não foi possível abrir os detalhes da vaga {vaga_id}: {erro}")

        descricao = self._descricao(titulo)
        if not descricao_relevante(descricao):
            return

        modelo = "Híbrido" if "híbrido" in localidade.casefold() else (
            "Remoto" if "remoto" in localidade.casefold() else "Presencial/Não informado"
        )
        mensagem = (
            "🔥 <b>Nova vaga no LinkedIn!</b>\n\n"
            f"📌 <b>{escape(titulo)}</b>\n"
            f"🏢 {escape(empresa)}\n"
            f"📍 {escape(localidade)}\n"
            f"💼 {escape(modelo)}\n"
            f"🔗 {escape(link_vaga)}"
        )

        vaga = Vaga(
            vaga_id=vaga_id,
            fonte=self.fonte,
            titulo=titulo,
            empresa=empresa,
            localidade=localidade,
            modelo_trabalho=modelo,
            descricao=descricao,
            link_vaga=link_vaga,
            mensagem=mensagem,
        )
        if self.salvar_vaga(vaga):
            print(f"Vaga salva: {titulo} — {empresa} ({vaga_id})")

    def executar(self):
        self.iniciar_navegador(storage_state=self._storage_state())
        try:
            self.page.goto(URL_BUSCA, wait_until="domcontentloaded")
            # O HTML atual repete componentkey no botão externo e na div interna.
            # Restringir ao botão seleciona um único card por vaga.
            cards_seletor = "[role='button'][componentkey^='job-card-component-ref-']"
            try:
                self.page.wait_for_selector(cards_seletor, timeout=30000)
            except Exception as erro:
                if "/login" in self.page.url:
                    raise RuntimeError(
                        "Sessão do LinkedIn expirada. Gere um novo LINKEDIN_LOG."
                    ) from erro
                print("Nenhum card de vaga apareceu na busca do LinkedIn.")
                print(self._texto(self.page.locator("body"))[:1000])
                return

            for pagina in range(MAX_PAGINAS):
                cards = self.page.locator(cards_seletor)
                quantidade = min(cards.count(), MAX_VAGAS_POR_PAGINA)
                print(f"Página {pagina + 1}: {quantidade} cards do LinkedIn.")

                for indice in range(quantidade):
                    try:
                        self._processar_card(cards.nth(indice))
                    except Exception as erro:
                        print(f"Erro ao processar card {indice + 1}: {erro}")

                proxima = self.page.get_by_role("button", name=re.compile("Próxima", re.I))
                if (
                    pagina + 1 >= MAX_PAGINAS
                    or not proxima.count()
                    or not proxima.is_enabled()
                ):
                    break

                proxima.click()
                self.page.wait_for_timeout(1500)
        finally:
            self.fechar_navegador()
