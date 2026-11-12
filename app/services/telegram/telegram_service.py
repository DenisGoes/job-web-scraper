from datetime import datetime, timedelta, timezone
from html import escape, unescape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import traceback

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from app.config.settings import (
    API_TOKEN,
    CANAL_ID,
    CANAL_ID_ANALISE,
    GEMINI_API_KEY,
    TOKEN_TELEGRAM_ANALISE,
)
from app.database.connection import SessionLocal, engine
from app.database.model import AnaliseVaga, Base, Vaga
from app.services.ia.analise.analise_service import AnaliseService
from app.services.ia.curriculos.gerador_curriculo import GeradorCurriculo

for nome_var, valor in (
    ("API_TOKEN", API_TOKEN),
    ("CANAL_ID", CANAL_ID),
    ("TOKEN_TELEGRAM_ANALISE", TOKEN_TELEGRAM_ANALISE),
    ("CANAL_ID_ANALISE", CANAL_ID_ANALISE),
    ("GEMINI_API_KEY", GEMINI_API_KEY),
):
    if not valor:
        raise ValueError(f"{nome_var} não configurado no ambiente.")

Base.metadata.create_all(bind=engine, checkfirst=True)

analise_service = AnaliseService()
gerador_curriculo = GeradorCurriculo()

bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=8)
bot_analise = telebot.TeleBot(TOKEN_TELEGRAM_ANALISE, threaded=True, num_threads=4)

ERROS_TELEGRAM_DELECAO_IGNORAVEIS = (
    "message to delete not found",
    "message not found",
    "message can't be deleted",
    "message identifier is not specified",
)

ERROS_CALLBACK_IGNORAVEIS = (
    "query is too old",
    "query id is invalid",
)

SCRAPERS_DISPONIVEIS = {
    "santander": ("🏦 Santander", "app.scrapers.santander_scraper"),
    "bradesco": ("🏦 Bradesco", "app.scrapers.bradesco_scraper"),
    "itau": ("🏦 Itaú", "app.scrapers.itau_scraper"),
    "infojobs": ("💼 InfoJobs", "app.scrapers.infojobs_scraper"),
    "linkedin": ("🔗 LinkedIn", "app.scrapers.linkedin_scraper"),
}

_SCRAPER_LOCK = threading.Lock()


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _montar_markup_vaga(vaga_id: int, status: str = "enviada"):
    rotulo_aplicada = "✅ Aplicada ✓" if status == "aplicada" else "✅ Aplicada"
    rotulo_salva = "⭐ Salva ✓" if status == "salva" else "⭐ Salva"
    return quick_markup(
        {
            rotulo_aplicada: {"callback_data": f"aplicada:{vaga_id}"},
            rotulo_salva: {"callback_data": f"salva:{vaga_id}"},
            "❌ Rejeitada": {"callback_data": f"rejeitada:{vaga_id}"},
            "🤖 Analisar vaga com IA": {"callback_data": f"analisar:{vaga_id}"},
        },
        row_width=2,
    )


def _montar_markup_scrapers():
    botoes = {
        rotulo: {"callback_data": f"scraper:{chave}"}
        for chave, (rotulo, _) in SCRAPERS_DISPONIVEIS.items()
    }
    botoes["🚀 Rodar Todos"] = {"callback_data": "scraper:todos"}
    return quick_markup(botoes, row_width=2)


def enviar_painel_scrapers(chat_id: str | int = CANAL_ID) -> None:
    """Envia ao canal o painel interativo para disparar os scrapers sob demanda."""
    bot.send_message(
        chat_id,
        "⚙️ <b>Painel de Scrapers</b>\nEscolha qual fonte deseja executar agora:",
        reply_markup=_montar_markup_scrapers(),
        parse_mode="HTML",
    )


def _executar_scrapers_background(alvo: str) -> None:
    if not _SCRAPER_LOCK.acquire(blocking=False):
        bot.send_message(
            CANAL_ID,
            "⏳ Já existe uma execução de scraper em andamento. Aguarde finalizar.",
        )
        return

    try:
        modulos = (
            list(SCRAPERS_DISPONIVEIS.values())
            if alvo == "todos"
            else [SCRAPERS_DISPONIVEIS[alvo]]
        )

        nomes = ", ".join(rotulo for rotulo, _ in modulos)
        bot.send_message(
            CANAL_ID, f"🚀 Iniciando coleta: <b>{nomes}</b>...", parse_mode="HTML"
        )

        falhas = []
        for rotulo, modulo in modulos:
            print(f"[Scraper Manual] Executando {modulo}...", flush=True)
            resultado = subprocess.run(
                [sys.executable, "-u", "-m", modulo],
                capture_output=False,
            )
            if resultado.returncode != 0:
                falhas.append(rotulo)

        enviar_novas_vagas()

        if falhas:
            bot.send_message(
                CANAL_ID,
                f"⚠️ Coleta concluída com avisos em: {', '.join(falhas)}. Vagas novas enviadas.",
            )
        else:
            bot.send_message(
                CANAL_ID,
                f"✅ Coleta finalizada com sucesso ({nomes})! Novas vagas enviadas acima.",
            )
    except Exception as e:
        traceback.print_exc()
        bot.send_message(CANAL_ID, f"❌ Erro ao executar scraper: {e}")
    finally:
        _SCRAPER_LOCK.release()


def _atualizar_botoes_mensagem(
    message_id: int | None, vaga_id: int, status: str
) -> None:
    if not message_id:
        return
    try:
        bot.edit_message_reply_markup(
            chat_id=CANAL_ID,
            message_id=message_id,
            reply_markup=_montar_markup_vaga(vaga_id, status),
        )
    except ApiTelegramException as e:
        if "message is not modified" not in str(e).lower():
            print(f"Aviso ao atualizar botões da vaga {vaga_id}: {e}", flush=True)


def _responder_callback(
    telegram_bot: telebot.TeleBot, call_id: str, texto: str
) -> None:
    try:
        telegram_bot.answer_callback_query(call_id, texto)
    except ApiTelegramException as e:
        descricao = str(getattr(e, "description", "") or e).lower()
        if any(err in descricao for err in ERROS_CALLBACK_IGNORAVEIS):
            print(
                f"Aviso Telegram: callback expirado ({descricao}), prosseguindo.",
                flush=True,
            )
        else:
            print(f"Aviso Telegram ao responder callback: {e}", flush=True)
    except Exception as e:
        print(f"Falha inesperada ao responder callback: {e}", flush=True)


def _lista_bullets(itens: list) -> str:
    return "\n".join(f"• {escape(str(item))}" for item in itens if item)


def formatar_analise(analise: dict, vaga: Vaga) -> str:
    classificacao = analise.get("classificacao_vaga", {})
    compatibilidade = analise.get("compatibilidade", {})
    candidatura = analise.get("candidatura", {})
    nivel = analise.get("nivel", {})
    resumo = analise.get("resumo_final", {})
    resumo_profissional = analise.get("resumo_profissional", {})
    habilidades = analise.get("habilidades", {})
    projetos = analise.get("projetos", {})
    ats = analise.get("ats", {})

    partes = [
        (
            f"🤖 ANÁLISE ATS DA VAGA\n\n"
            f"💼 {escape(str(vaga.titulo))}\n"
            f"🏢 {escape(str(vaga.empresa or 'Não informada'))}\n"
            f"📍 {escape(str(vaga.localidade or 'Não informada'))}\n"
            f"🔗 {escape(str(vaga.link_vaga or 'Link não informado'))}\n\n"
            f"📝 DESCRIÇÃO DA VAGA\n{escape(str(vaga.descricao or 'Não informada'))}"
        ),
        (
            f"📊 COMPATIBILIDADE: {compatibilidade.get('porcentagem', 0)}%\n"
            f"{escape(str(compatibilidade.get('motivo', '')))}"
        ),
        (
            f"🎯 CANDIDATURA: {escape(str(candidatura.get('recomendacao', '')))}\n"
            f"{escape(str(candidatura.get('motivo', '')))}"
        ),
        (
            f"🧭 CLASSIFICAÇÃO\n"
            f"• Área principal: {escape(str(classificacao.get('area_principal', '')))}\n"
            f"• Área secundária: {escape(str(classificacao.get('area_secundaria', '')))}\n"
            f"• Nível: {escape(str(classificacao.get('nivel', '')))}\n"
            f"• Modalidade: {escape(str(classificacao.get('modalidade', '')))}\n"
            f"• Adequada para estudante: {'Sim' if classificacao.get('adequada_para_estudante') else 'Não'}\n"
            f"{escape(str(classificacao.get('observacoes', '')))}"
        ),
        (
            f"📈 COMPARAÇÃO DE NÍVEL\n"
            f"• Vaga: {escape(str(nivel.get('nivel_vaga', '')))}\n"
            f"• Candidato: {escape(str(nivel.get('nivel_candidato', '')))}\n"
            f"{escape(str(nivel.get('comparacao', '')))}\n"
            f"{escape(str(nivel.get('observacao', '')))}"
        ),
    ]

    if pontos_fortes := analise.get("pontos_fortes"):
        linhas = ["✅ PONTOS FORTES"]
        for p in pontos_fortes:
            linhas.append(
                f"• {escape(str(p.get('titulo', '')))}: {escape(str(p.get('descricao', '')))} "
                f"(Relevância: {escape(str(p.get('relevancia', '')))})"
            )
        partes.append("\n".join(linhas))

    if pontos_fracos := analise.get("pontos_fracos"):
        linhas = ["⚠️ PONTOS FRACOS E LACUNAS"]
        for p in pontos_fracos:
            vale = "Sim" if p.get("vale_estudar") else "Não"
            linhas.append(
                f"• {escape(str(p.get('titulo', '')))}: {escape(str(p.get('descricao', '')))} "
                f"[Impacto: {escape(str(p.get('impacto', '')))} | Vale estudar: {vale}]"
            )
        partes.append("\n".join(linhas))

    for chave, titulo_secao in (
        ("requisitos_obrigatorios", "📋 REQUISITOS OBRIGATÓRIOS"),
        ("requisitos_desejaveis", "⭐ REQUISITOS DESEJÁVEIS"),
    ):
        if itens := analise.get(chave):
            linhas = [titulo_secao]
            for req in itens:
                linhas.append(
                    f"• {escape(str(req.get('requisito', '')))} — "
                    f"Status: {escape(str(req.get('status', '')))} | "
                    f"Evidência: {escape(str(req.get('evidencia', '')))}"
                )
            partes.append("\n".join(linhas))

    partes.append(
        f"👤 RESUMO PROFISSIONAL\n"
        f"Atual: {escape(str(resumo_profissional.get('atual', '')))}\n"
        f"Melhorias: {escape(str(resumo_profissional.get('melhorias', '')))}\n"
        f"Sugestão: {escape(str(resumo_profissional.get('sugestao', '')))}"
    )

    secoes_hab = ["🛠️ HABILIDADES"]
    for campo, rotulo in (
        ("manter", "Manter"),
        ("priorizar", "Priorizar"),
        ("reorganizar", "Reorganizar"),
        ("remover", "Remover"),
    ):
        if lista := habilidades.get(campo):
            secoes_hab.append(f"{rotulo}:\n{_lista_bullets(lista)}")
    if obs_hab := habilidades.get("observacoes"):
        secoes_hab.append(escape(str(obs_hab)))
    partes.append("\n".join(secoes_hab))

    if projetos.get("mais_relevantes") or projetos.get("melhorias"):
        secoes_proj = ["💻 PROJETOS"]
        if rel := projetos.get("mais_relevantes"):
            secoes_proj.append(f"Mais relevantes:\n{_lista_bullets(rel)}")
        if mel := projetos.get("melhorias"):
            secoes_proj.append(f"Melhorias:\n{_lista_bullets(mel)}")
        partes.append("\n".join(secoes_proj))

    if (
        ats.get("presentes")
        or ats.get("ausentes")
        or ats.get("termos_exatos_vaga")
    ):
        secoes_ats = ["🤖 PALAVRAS-CHAVE ATS"]
        if pres := ats.get("presentes"):
            secoes_ats.append(f"Presentes:\n{_lista_bullets(pres)}")
        if exatos := ats.get("termos_exatos_vaga"):
            secoes_ats.append(f"Termos exatos da vaga:\n{_lista_bullets(exatos)}")
        if aus := ats.get("ausentes"):
            secoes_ats.append(f"Ausentes:\n{_lista_bullets(aus)}")
        partes.append("\n".join(secoes_ats))

    if estudos := analise.get("estudos"):
        ordenados = sorted(estudos, key=lambda item: item.get("prioridade", 999))
        linhas = ["📚 ESTUDOS RECOMENDADOS"]
        for est in ordenados:
            linhas.append(
                f"• [P{escape(str(est.get('prioridade', '')))}] "
                f"{escape(str(est.get('titulo', '')))} — {escape(str(est.get('motivo', '')))}"
            )
        partes.append("\n".join(linhas))

    if plano := analise.get("plano_acao"):
        partes.append(f"🚀 PLANO DE AÇÃO\n{_lista_bullets(plano)}")

    partes.append(
        f"🏁 RESUMO FINAL\n"
        f"• Maior qualidade: {escape(str(resumo.get('maior_qualidade', '')))}\n"
        f"• Maior lacuna: {escape(str(resumo.get('maior_lacuna', '')))}\n"
        f"• Maior ponto de melhoria: {escape(str(resumo.get('maior_ponto_melhoria', '')))}\n"
        f"• Principal estudo: {escape(str(resumo.get('principal_estudo', '')))}\n"
        f"• Nota final: {escape(str(resumo.get('nota_final', 0)))}/100\n"
        f"• Candidatura recomendada: {'Sim' if resumo.get('candidatura_recomendada') else 'Não'}"
    )

    return "\n\n".join(partes)


def enviar_analise(analise: dict, vaga: Vaga, session=None) -> None:
    if session is not None:
        registro = session.query(AnaliseVaga).filter_by(vaga_id=vaga.id).first()
        if registro is None:
            registro = AnaliseVaga(vaga_id=vaga.id)
            session.add(registro)
        registro.resultado_json = json.dumps(analise, ensure_ascii=False)
        session.commit()

    mensagem_texto = unescape(re.sub(r"<[^>]*>", "", formatar_analise(analise, vaga)))
    limite = 4000
    partes = []

    while mensagem_texto:
        corte = min(limite, len(mensagem_texto))
        if corte < len(mensagem_texto):
            quebra = mensagem_texto.rfind("\n", 0, corte)
            if quebra > 0:
                corte = quebra
        partes.append(mensagem_texto[:corte])
        mensagem_texto = mensagem_texto[corte:].lstrip()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "📄 Gerar currículo", callback_data=f"curriculo:{vaga.id}"
        )
    )

    for indice, parte in enumerate(partes):
        bot_analise.send_message(
            CANAL_ID_ANALISE,
            parte,
            reply_markup=markup if indice == len(partes) - 1 else None,
        )


@bot.message_handler(
    func=lambda m: bool(m.text) and m.text.strip().lower().startswith("/scrapers")
)
@bot.channel_post_handler(
    func=lambda m: bool(m.text) and m.text.strip().lower().startswith("/scrapers")
)
def comando_scrapers(message):
    print(f"[Telegram] Comando /scrapers recebido de chat {message.chat.id}", flush=True)
    enviar_painel_scrapers(message.chat.id)


@bot_analise.callback_query_handler(func=lambda call: True)
def callback_curriculo(call):
    with SessionLocal() as session:
        try:
            try:
                acao, vaga_id_str = call.data.split(":", 1)
                vaga_id = int(vaga_id_str)
            except (ValueError, AttributeError):
                _responder_callback(bot_analise, call.id, "❌ Ação inválida.")
                return

            if acao != "curriculo":
                _responder_callback(bot_analise, call.id, "❌ Ação inválida.")
                return

            vaga = session.query(Vaga).filter_by(id=vaga_id).first()
            registro = session.query(AnaliseVaga).filter_by(vaga_id=vaga_id).first()

            if not vaga or not registro:
                _responder_callback(
                    bot_analise, call.id, "❌ Análise da vaga não encontrada."
                )
                return

            _responder_callback(
                bot_analise, call.id, "📄 Gerando currículo personalizado…"
            )
            print(f"[Telegram] Gerando currículo da vaga {vaga.id}...", flush=True)

            texto = gerador_curriculo.gerar_texto(
                vaga, json.loads(registro.resultado_json)
            )

            with tempfile.TemporaryDirectory() as pasta:
                arquivo = Path(pasta) / f"curriculo_vaga_{vaga.id}.docx"
                gerador_curriculo.criar_docx(texto, arquivo)
                with arquivo.open("rb") as documento:
                    bot_analise.send_document(
                        CANAL_ID_ANALISE,
                        documento,
                        caption=f"Currículo personalizado — {vaga.titulo} | {vaga.empresa or ''}",
                    )
            print(f"[Telegram] Currículo da vaga {vaga.id} enviado!", flush=True)
        except Exception:
            traceback.print_exc()
            _responder_callback(bot_analise, call.id, "❌ Erro ao gerar o currículo.")
            try:
                bot_analise.send_message(
                    CANAL_ID_ANALISE,
                    "Não foi possível gerar o currículo. Tente novamente mais tarde.",
                )
            except Exception:
                pass


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        acao, alvo = call.data.split(":", 1)
    except (ValueError, AttributeError):
        _responder_callback(bot, call.id, "❌ Ação inválida.")
        return

    if acao == "scraper":
        if alvo != "todos" and alvo not in SCRAPERS_DISPONIVEIS:
            _responder_callback(bot, call.id, "❌ Scraper desconhecido.")
            return

        if _SCRAPER_LOCK.locked():
            _responder_callback(
                bot, call.id, "⏳ Já há um scraper rodando no momento."
            )
            return

        _responder_callback(bot, call.id, "🚀 Disparando scraper em segundo plano...")
        threading.Thread(
            target=_executar_scrapers_background,
            args=(alvo,),
            daemon=True,
        ).start()
        return

    try:
        vaga_id = int(alvo)
    except ValueError:
        _responder_callback(bot, call.id, "❌ ID de vaga inválido.")
        return

    with SessionLocal() as session:
        try:
            vaga = session.query(Vaga).filter_by(id=vaga_id).first()
            if not vaga:
                _responder_callback(bot, call.id, "❌ Vaga não encontrada.")
                return

            agora = _agora_utc()
            print(
                f"[Telegram] Clique '{acao}' na vaga {vaga.id} ({vaga.titulo})",
                flush=True,
            )

            if acao == "analisar":
                _responder_callback(bot, call.id, "⏳ Processando análise ATS...")
                try:
                    analise = analise_service.analisar(vaga)
                    enviar_analise(analise, vaga, session)
                    print(
                        f"[Telegram] Análise enviada para o canal: {vaga.id}", flush=True
                    )
                except Exception:
                    traceback.print_exc()
                    _responder_callback(bot, call.id, "❌ Erro ao gerar análise.")

            elif acao == "salva":
                if vaga.status == "salva":
                    _responder_callback(bot, call.id, "⭐ Essa vaga já está salva.")
                elif vaga.status == "aplicada":
                    _responder_callback(bot, call.id, "✅ Essa vaga já foi aplicada.")
                else:
                    vaga.status = "salva"
                    vaga.data_salva = agora
                    vaga.remover_em = agora + timedelta(days=5)
                    session.commit()
                    _atualizar_botoes_mensagem(
                        vaga.telegram_message_id, vaga.id, "salva"
                    )
                    _responder_callback(
                        bot,
                        call.id,
                        "⭐ Vaga salva! (Será removida em 5 dias se não aplicada)",
                    )

            elif acao == "aplicada":
                if vaga.status == "aplicada":
                    _responder_callback(bot, call.id, "✅ Essa vaga já foi aplicada.")
                else:
                    vaga.status = "aplicada"
                    vaga.data_aplicada = agora
                    vaga.remover_em = agora + timedelta(days=8)
                    session.commit()
                    _atualizar_botoes_mensagem(
                        vaga.telegram_message_id, vaga.id, "aplicada"
                    )
                    _responder_callback(
                        bot,
                        call.id,
                        "✅ Vaga marcada como aplicada! (Mantida por 8 dias)",
                    )

            elif acao in ("rejeitada", "excluida"):
                vaga.status = "excluida"
                session.commit()

                mensagem_apagada = True
                if vaga.telegram_message_id:
                    try:
                        bot.delete_message(CANAL_ID, vaga.telegram_message_id)
                    except ApiTelegramException as e:
                        descricao = str(getattr(e, "description", "") or e).lower()
                        if any(
                            err in descricao
                            for err in ERROS_TELEGRAM_DELECAO_IGNORAVEIS
                        ):
                            mensagem_apagada = False
                        else:
                            _responder_callback(
                                bot,
                                call.id,
                                "Erro de rede no Telegram. Tente novamente.",
                            )
                            return

                session.delete(vaga)
                session.commit()

                _responder_callback(
                    bot,
                    call.id,
                    "❌ Vaga excluída do banco e do canal."
                    if mensagem_apagada
                    else "❌ Vaga excluída do banco (mensagem com +48h permanece no canal).",
                )

            else:
                _responder_callback(bot, call.id, "❌ Ação desconhecida.")

        except Exception:
            session.rollback()
            traceback.print_exc()
            _responder_callback(bot, call.id, "❌ Ocorreu um erro.")


def enviar_vaga(vaga: Vaga, max_tentativas: int = 3) -> bool:
    markup = _montar_markup_vaga(vaga.id, status="enviada")

    for _ in range(max_tentativas):
        try:
            message = bot.send_message(
                CANAL_ID,
                vaga.mensagem,
                reply_markup=markup,
                parse_mode="HTML",
            )
            vaga.telegram_message_id = message.message_id
            return True

        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result_json.get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after + 1)
            else:
                print(f"Erro ao enviar vaga {vaga.id}: {e}", flush=True)
                return False

        except Exception:
            traceback.print_exc()
            return False

    return False


def enviar_novas_vagas() -> None:
    with SessionLocal() as session:
        try:
            vagas = session.query(Vaga).filter_by(status="nova").all()

            for indice, vaga in enumerate(vagas, start=1):
                print(
                    f"Enviando vaga {indice}/{len(vagas)} ao Telegram: {vaga.titulo}",
                    flush=True,
                )

                if enviar_vaga(vaga):
                    agora = _agora_utc()
                    vaga.status = "enviada"
                    vaga.remover_em = agora + timedelta(days=5)
                    session.commit()
                else:
                    session.rollback()

                time.sleep(1.5)

        except Exception:
            session.rollback()
            traceback.print_exc()