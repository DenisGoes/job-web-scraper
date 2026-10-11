import hashlib
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

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
                estado = json.loads(LINKEDIN_LOG)
            except (json.JSONDecodeError, TypeError) as erro:
                raise RuntimeError(
                    "LINKEDIN_LOG não contém JSON válido. Cole no secret o "
                    "conteúdo completo de linkedin_log.json."
                ) from erro

            if not isinstance(estado, dict):
                raise RuntimeError("LINKEDIN_LOG precisa ser um JSON de storage_state.")

            cookies = estado.get("cookies", [])
            if not isinstance(cookies, list):
                cookies = []
            tem_cookie_sessao = any(
                cookie.get("name") == "li_at"
                for cookie in cookies
                if isinstance(cookie, dict)
            )
            print(
                "LINKEDIN_LOG recebido: "
                f"{len(cookies)} cookies; cookie de autenticação li_at: "
                f"{'presente' if tem_cookie_sessao else 'ausente'}."
            )
            if not tem_cookie_sessao:
                raise RuntimeError(
                    "LINKEDIN_LOG foi recebido, mas não contém o cookie li_at. "
                    "Gere um novo estado de sessão depois de entrar no LinkedIn."
                )
            return estado

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
                return re.sub(r"\s+", " ", locator.first.inner_text()).strip()
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

    def _ler_card(self, card):
        """Captura os dados da listagem antes de abrir detalhes e alterar o DOM."""
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

        return {
            "vaga_id": vaga_id,
            "titulo": titulo,
            "empresa": empresa,
            "localidade": localidade,
            "publico": False,
        }

    def _ler_cards_publicos(self, cards):
        """Extrai os cards públicos em uma avaliação do DOM, sem waits por card."""
        registros = cards.evaluate_all(
            """items => items.map(item => {
                let card = item.closest('[componentkey^="job-card-component-ref-"]')
                    || item.closest('[class*="base-card"]')
                    || item.closest('li')
                    || item.parentElement;
                const texto = node => (node?.innerText || '')
                    .replace(/\\s+/g, ' ').trim();
                const linhasDe = node => (node?.innerText || '')
                    .split(/\\n+/)
                    .map(linha => linha.replace(/\\s+/g, ' ').trim())
                    .filter(Boolean)
                    .filter((linha, indice, todas) => indice === 0 || linha !== todas[indice - 1]);
                const temChaveDeCard = Boolean(
                    item.closest('[componentkey^="job-card-component-ref-"]')
                );
                if (!temChaveDeCard) {
                    let ancestral = item.parentElement;
                    for (let nivel = 0; ancestral && nivel < 6; nivel++, ancestral = ancestral.parentElement) {
                        const linhasAncestral = linhasDe(ancestral);
                        if (linhasAncestral.length >= 3 && linhasAncestral.length <= 12) {
                            card = ancestral;
                            break;
                        }
                    }
                }
                const componentKey = card?.getAttribute('componentkey')
                    || item.getAttribute('componentkey') || '';
                const href = item.href || item.querySelector('a[href]')?.href || '';
                const linhas = linhasDe(card) || linhasDe(item);
                const paragrafos = [...(card?.querySelectorAll('p') || [])];
                const tituloParagrafo = paragrafos[0];
                const titulo = texto(tituloParagrafo?.querySelector(
                    'span:not([aria-hidden="true"])'
                )) || texto(tituloParagrafo);
                const url = new URL(href || location.href, location.origin);
                const segmentoVaga = url.pathname.match(/\\/jobs\\/view\\/([^/]+)/)?.[1] || '';
                const id = componentKey.match(/job-card-component-ref-(\\d+)/)?.[1]
                    || card?.getAttribute('data-job-id')
                    || item.getAttribute('data-job-id')
                    || url.searchParams.get('currentJobId')
                    || segmentoVaga.match(/(\\d{6,})$/)?.[1]
                    || segmentoVaga;
                const tituloFinal = titulo || texto(card?.querySelector(
                    '.base-search-card__title, h3, [class*="title"]'
                )) || linhas[0] || texto(item);
                const localidade = texto(card?.querySelector(
                    '.job-search-card__location, .base-search-card__location'
                )) || (componentKey.startsWith('job-card-component-ref-')
                    ? texto(paragrafos[2])
                    : '') || linhas.find(linha =>
                    linha !== tituloFinal
                    && /\\b(?:SP|RJ|MG|ES|PR|SC|RS|DF|BA|PE|CE|GO|AM|PA|Brasil)\\b|\\b(?:remoto|h[ií]brido|presencial)\\b/i.test(linha)
                ) || 'Localidade não informada';
                const empresa = texto(card?.querySelector(
                    '.base-search-card__subtitle, h4'
                )) || (componentKey.startsWith('job-card-component-ref-')
                    ? texto(paragrafos[1])
                    : '') || linhas.find(linha =>
                    linha !== tituloFinal
                    && linha !== localidade
                    && !/\\b(?:há|today|yesterday|days? ago|weeks? ago|months? ago)\\b/i.test(linha)
                ) || 'Empresa não informada';
                return {
                    vaga_id: id,
                    titulo: tituloFinal,
                    empresa,
                    localidade,
                    href,
                    publico: true
                };
            })"""
        )
        unicos = {}
        for registro in registros:
            vaga_id = registro.get("vaga_id")
            href = registro.get("href") or ""
            if not vaga_id and "/jobs/view/" in href:
                partes_url = urlsplit(href)
                caminho = partes_url.path.rstrip("/")
                vaga_id = f"li-{hashlib.sha256(caminho.encode()).hexdigest()[:20]}"
                registro["vaga_id"] = vaga_id
                registro["link_vaga"] = urlunsplit(
                    (partes_url.scheme, partes_url.netloc, caminho + "/", "", "")
                )
            if vaga_id and registro.get("titulo"):
                unicos[vaga_id] = registro
        if not unicos and registros:
            print(
                "LinkedIn retornou cards, mas não consegui extrair título/ID. "
                f"Amostra: {registros[0]}"
            )
        return list(unicos.values())[:MAX_VAGAS_POR_PAGINA]

    def _processar_card(self, dados):
        vaga_id = dados["vaga_id"]
        titulo = dados["titulo"]
        empresa = dados["empresa"]
        localidade = dados["localidade"]

        # O cartão novo usa classes geradas; o componentkey contém o ID estável.
        link_vaga = dados.get("link_vaga") or (
            f"https://www.linkedin.com/jobs/view/{vaga_id}/"
        )

        if not titulo or not titulo_relevante(titulo):
            return

        try:
            # Reencontra o card pelo ID após eventuais atualizações da listagem.
            if not dados.get("publico"):
                card = self.page.locator(
                    f"[role='button'][componentkey='job-card-component-ref-{vaga_id}']"
                ).first
                card.wait_for(state="attached", timeout=5000)
                card.scroll_into_view_if_needed(timeout=5000)
                card.click(timeout=5000)
                self.page.wait_for_timeout(1200)
        except Exception as erro:
            print(f"Não foi possível abrir os detalhes da vaga {vaga_id}: {erro}")

        if dados.get("publico"):
            descricao = (
                "Descrição completa indisponível na busca pública do LinkedIn. "
                "Consulte a vaga no link."
            )
        else:
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
            self.page.set_default_timeout(10000)
            self.page.goto(
                URL_BUSCA,
                wait_until="domcontentloaded",
                timeout=30000,
            )
            # O HTML atual repete componentkey no botão externo e na div interna.
            # Restringir ao botão seleciona um único card por vaga.
            cards_seletor = "[role='button'][componentkey^='job-card-component-ref-']"
            cards_publicos_seletor = (
                "[role='button'][componentkey^='job-card-component-ref-'], "
                "a[href*='/jobs/view/']"
            )
            cards_publicos = False
            try:
                self.page.wait_for_selector(cards_seletor, timeout=10000)
            except Exception as erro:
                try:
                    self.page.wait_for_selector(cards_publicos_seletor, timeout=10000)
                    cards_publicos = True
                    print(
                        "LinkedIn sem sessão autenticada; usando os cards públicos "
                        "da busca."
                    )
                except Exception:
                    corpo = self._texto(self.page.locator("body"))[:1000]
                    if "/login" in self.page.url or "Entre para criar um alerta" in corpo:
                        raise RuntimeError(
                            "LinkedIn exibiu a busca pública, mas não carregou os "
                            "cards de vagas. Atualize o secret LINKEDIN_LOG no GitHub."
                        ) from erro
                    print("Nenhum card de vaga apareceu na busca do LinkedIn.")
                    print(corpo)
                    return

            for pagina in range(MAX_PAGINAS):
                seletor_atual = cards_publicos_seletor if cards_publicos else cards_seletor
                cards = self.page.locator(seletor_atual)
                quantidade = min(cards.count(), MAX_VAGAS_POR_PAGINA)
                print(f"Página {pagina + 1}: {quantidade} cards do LinkedIn.")

                # Ler todos os dados antes dos cliques: abrir um detalhe pode
                # fazer o LinkedIn recriar ou virtualizar os cards da listagem.
                if cards_publicos:
                    dados_cards = self._ler_cards_publicos(
                        self.page.locator(cards_publicos_seletor)
                    )
                else:
                    dados_cards = []
                    for indice in range(quantidade):
                        try:
                            dados = self._ler_card(cards.nth(indice))
                            if dados:
                                dados_cards.append(dados)
                        except Exception as erro:
                            print(f"Erro ao ler card {indice + 1}: {erro}")

                print(f"Dados lidos: {len(dados_cards)} vagas.")

                for indice, dados in enumerate(dados_cards, start=1):
                    try:
                        print(
                            f"Processando vaga {indice}/{len(dados_cards)}: "
                            f"{dados['titulo']}"
                        )
                        self._processar_card(dados)
                    except Exception as erro:
                        print(f"Erro ao processar card {indice}: {erro}")

                proxima = self.page.get_by_role(
                    "button", name=re.compile("Próxima|Next", re.I)
                )
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
