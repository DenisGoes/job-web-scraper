from datetime import datetime, timedelta, timezone
from html import escape
import time
import traceback

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from app.config.settings import (
    API_TOKEN,
    CANAL_ID,
    TOKEN_TELEGRAM_ANALISE,
    CANAL_ID_ANALISE
)
from app.database.connection import SessionLocal
from app.database.model import Vaga
from app.services.IA.analise.analise_service import AnaliseService


if not API_TOKEN:
    raise ValueError("API_TOKEN não configurado.")

if not TOKEN_TELEGRAM_ANALISE:
    raise ValueError(
        "TOKEN_TELEGRAM_ANALISE não configurado."
    )

if not CANAL_ID_ANALISE:
    raise ValueError(
        "CANAL_ID_ANALISE não configurado."
    )


analise_service = AnaliseService()

bot = telebot.TeleBot(API_TOKEN)

bot_analise = telebot.TeleBot(
    TOKEN_TELEGRAM_ANALISE
)


def formatar_analise(analise, vaga):

    classificacao = analise.get(
        "classificacao_vaga",
        {}
    )

    compatibilidade = analise.get(
        "compatibilidade",
        {}
    )

    candidatura = analise.get(
        "candidatura",
        {}
    )

    nivel = analise.get(
        "nivel",
        {}
    )

    resumo = analise.get(
        "resumo_final",
        {}
    )

    resumo_profissional = analise.get(
        "resumo_profissional",
        {}
    )

    habilidades = analise.get(
        "habilidades",
        {}
    )

    projetos = analise.get(
        "projetos",
        {}
    )

    requisitos_obrigatorios = analise.get(
        "requisitos_obrigatorios",
        []
    )

    requisitos_desejaveis = analise.get(
        "requisitos_desejaveis",
        []
    )

    pontos_fortes = analise.get(
        "pontos_fortes",
        []
    )

    pontos_fracos = analise.get(
        "pontos_fracos",
        []
    )

    estudos = analise.get(
        "estudos",
        []
    )

    plano_acao = analise.get(
        "plano_acao",
        []
    )

    ats = analise.get(
        "ats",
        {}
    )

    partes = []

    partes.append(
        f"🤖 <b>ANÁLISE DA VAGA</b>\n\n"
        f"💼 <b>{escape(str(vaga.titulo))}</b>\n"
        f"🏢 {escape(str(vaga.empresa))}\n"
        f"📍 {escape(str(vaga.localidade))}"
    )

    partes.append(
        "📊 <b>COMPATIBILIDADE</b>\n\n"
        f"<b>{compatibilidade.get('porcentagem', 0)}%</b>\n"
        f"{escape(str(compatibilidade.get('motivo', '')))}"
    )

    partes.append(
        "🎯 <b>CANDIDATURA</b>\n\n"
        f"<b>{escape(str(candidatura.get('recomendacao', '')))}</b>\n"
        f"{escape(str(candidatura.get('motivo', '')))}"
    )

    partes.append(
        "🧭 <b>CLASSIFICAÇÃO</b>\n\n"
        f"Área principal: "
        f"<b>{escape(str(classificacao.get('area_principal', '')))}</b>\n"
        f"Área secundária: "
        f"{escape(str(classificacao.get('area_secundaria', '')))}\n"
        f"Nível: "
        f"{escape(str(classificacao.get('nivel', '')))}\n"
        f"Modalidade: "
        f"{escape(str(classificacao.get('modalidade', '')))}\n"
        f"Adequada para estudante: "
        f"{'Sim' if classificacao.get('adequada_para_estudante') else 'Não'}\n\n"
        f"{escape(str(classificacao.get('observacoes', '')))}"
    )

    partes.append(
        "📈 <b>NÍVEL</b>\n\n"
        f"Nível da vaga: "
        f"<b>{escape(str(nivel.get('nivel_vaga', '')))}</b>\n"
        f"Nível do candidato: "
        f"<b>{escape(str(nivel.get('nivel_candidato', '')))}</b>\n\n"
        f"{escape(str(nivel.get('comparacao', '')))}\n\n"
        f"{escape(str(nivel.get('observacao', '')))}"
    )

    if pontos_fortes:

        texto = "✅ <b>PONTOS FORTES</b>\n"

        for ponto in pontos_fortes:

            texto += (
                f"\n<b>• {escape(str(ponto.get('titulo', '')))}</b>\n"
                f"{escape(str(ponto.get('descricao', '')))}\n"
                f"Relevância: "
                f"{escape(str(ponto.get('relevancia', '')))}\n"
            )

        partes.append(texto)

    if pontos_fracos:

        texto = "⚠️ <b>PONTOS FRACOS E LACUNAS</b>\n"

        for ponto in pontos_fracos:

            texto += (
                f"\n<b>• {escape(str(ponto.get('titulo', '')))}</b>\n"
                f"{escape(str(ponto.get('descricao', '')))}\n"
                f"Impacto: "
                f"{escape(str(ponto.get('impacto', '')))}\n"
                f"Vale estudar: "
                f"{'Sim' if ponto.get('vale_estudar') else 'Não'}\n"
            )

        partes.append(texto)

    if requisitos_obrigatorios:

        texto = "📋 <b>REQUISITOS OBRIGATÓRIOS</b>\n"

        for requisito in requisitos_obrigatorios:

            texto += (
                f"\n• <b>{escape(str(requisito.get('requisito', '')))}</b>\n"
                f"Status: "
                f"{escape(str(requisito.get('status', '')))}\n"
                f"Evidência: "
                f"{escape(str(requisito.get('evidencia', '')))}\n"
            )

        partes.append(texto)

    if requisitos_desejaveis:

        texto = "⭐ <b>REQUISITOS DESEJÁVEIS</b>\n"

        for requisito in requisitos_desejaveis:

            texto += (
                f"\n• <b>{escape(str(requisito.get('requisito', '')))}</b>\n"
                f"Status: "
                f"{escape(str(requisito.get('status', '')))}\n"
                f"Evidência: "
                f"{escape(str(requisito.get('evidencia', '')))}\n"
            )

        partes.append(texto)

    partes.append(
        "👤 <b>RESUMO PROFISSIONAL</b>\n\n"
        f"<b>Atual:</b>\n"
        f"{escape(str(resumo_profissional.get('atual', '')))}\n\n"
        f"<b>Melhorias:</b>\n"
        f"{escape(str(resumo_profissional.get('melhorias', '')))}\n\n"
        f"<b>Sugestão:</b>\n"
        f"{escape(str(resumo_profissional.get('sugestao', '')))}"
    )

    manter = habilidades.get("manter", [])
    priorizar = habilidades.get("priorizar", [])
    reorganizar = habilidades.get("reorganizar", [])
    remover = habilidades.get("remover", [])

    habilidades_texto = "🛠️ <b>HABILIDADES</b>\n"

    if manter:
        habilidades_texto += (
            "\n<b>Manter:</b>\n"
            + "\n".join(
                f"• {escape(str(item))}"
                for item in manter
            )
        )

    if priorizar:
        habilidades_texto += (
            "\n\n<b>Priorizar:</b>\n"
            + "\n".join(
                f"• {escape(str(item))}"
                for item in priorizar
            )
        )

    if reorganizar:
        habilidades_texto += (
            "\n\n<b>Reorganizar:</b>\n"
            + "\n".join(
                f"• {escape(str(item))}"
                for item in reorganizar
            )
        )

    if remover:
        habilidades_texto += (
            "\n\n<b>Remover:</b>\n"
            + "\n".join(
                f"• {escape(str(item))}"
                for item in remover
            )
        )

    habilidades_texto += (
        "\n\n"
        + escape(
            str(
                habilidades.get(
                    "observacoes",
                    ""
                )
            )
        )
    )

    partes.append(habilidades_texto)

    mais_relevantes = projetos.get(
        "mais_relevantes",
        []
    )

    melhorias_projetos = projetos.get(
        "melhorias",
        []
    )

    if mais_relevantes or melhorias_projetos:

        texto = "💻 <b>PROJETOS</b>\n"

        if mais_relevantes:

            texto += (
                "\n<b>Mais relevantes:</b>\n"
                + "\n".join(
                    f"• {escape(str(item))}"
                    for item in mais_relevantes
                )
            )

        if melhorias_projetos:

            texto += (
                "\n\n<b>Melhorias:</b>\n"
                + "\n".join(
                    f"• {escape(str(item))}"
                    for item in melhorias_projetos
                )
            )

        partes.append(texto)

    if ats:

        presentes = ats.get(
            "presentes",
            []
        )

        ausentes = ats.get(
            "ausentes",
            []
        )

        texto = "🤖 <b>ATS</b>\n"

        if presentes:

            texto += (
                "\n<b>Presentes:</b>\n"
                + "\n".join(
                    f"• {escape(str(item))}"
                    for item in presentes
                )
            )

        if ausentes:

            texto += (
                "\n\n<b>Ausentes:</b>\n"
                + "\n".join(
                    f"• {escape(str(item))}"
                    for item in ausentes
                )
            )

        partes.append(texto)

    if estudos:

        texto = "📚 <b>ESTUDOS RECOMENDADOS</b>\n"

        estudos_ordenados = sorted(
            estudos,
            key=lambda item: item.get(
                "prioridade",
                999
            )
        )

        for estudo in estudos_ordenados:

            texto += (
                f"\n<b>Prioridade "
                f"{escape(str(estudo.get('prioridade', '')))}</b> — "
                f"{escape(str(estudo.get('titulo', '')))}\n"
                f"{escape(str(estudo.get('motivo', '')))}\n"
            )

        partes.append(texto)

    if plano_acao:

        texto = "🚀 <b>PLANO DE AÇÃO</b>\n"

        for item in plano_acao:

            texto += (
                f"\n• {escape(str(item))}"
            )

        partes.append(texto)

    partes.append(
        "🏁 <b>RESUMO FINAL</b>\n\n"
        f"Maior qualidade:\n"
        f"{escape(str(resumo.get('maior_qualidade', '')))}\n\n"
        f"Maior lacuna:\n"
        f"{escape(str(resumo.get('maior_lacuna', '')))}\n\n"
        f"Maior ponto de melhoria:\n"
        f"{escape(str(resumo.get('maior_ponto_melhoria', '')))}\n\n"
        f"Principal estudo:\n"
        f"{escape(str(resumo.get('principal_estudo', '')))}\n\n"
        f"Nota final: "
        f"<b>{escape(str(resumo.get('nota_final', 0)))}/100</b>\n"
        f"Candidatura recomendada: "
        f"{'Sim' if resumo.get('candidatura_recomendada') else 'Não'}"
    )

    return "\n\n".join(partes)


def enviar_analise(analise, vaga):

    mensagem = formatar_analise(
        analise,
        vaga
    )

    limite = 4000

    partes = [
        mensagem[i:i + limite]
        for i in range(
            0,
            len(mensagem),
            limite
        )
    ]

    for parte in partes:

        bot_analise.send_message(
            CANAL_ID_ANALISE,
            parte,
            parse_mode="HTML"
        )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    session = SessionLocal()

    try:

        try:

            acao, vaga_id = call.data.split(":")
            vaga_id = int(vaga_id)

        except (ValueError, AttributeError):

            bot.answer_callback_query(
                call.id,
                "❌ Ação inválida."
            )

            return

        vaga = (
            session
            .query(Vaga)
            .filter_by(id=vaga_id)
            .first()
        )

        if not vaga:

            bot.answer_callback_query(
                call.id,
                "❌ Vaga não encontrada."
            )

            return

        if acao == "analisar":

            bot.answer_callback_query(
                call.id,
                "⏳ Processando análise..."
            )

            try:

                analise = analise_service.analisar(
                    vaga
                )

                enviar_analise(
                    analise,
                    vaga
                )

                print(
                    f"Análise enviada para o canal: "
                    f"{vaga.id}"
                )

            except Exception:

                traceback.print_exc()

                try:

                    bot.answer_callback_query(
                        call.id,
                        "❌ Erro ao gerar análise."
                    )

                except Exception:

                    pass

        elif acao == "salva":

            if vaga.status == "salva":

                bot.answer_callback_query(
                    call.id,
                    "⭐ Essa vaga já está salva."
                )

            elif vaga.status == "aplicada":

                bot.answer_callback_query(
                    call.id,
                    "✅ Essa vaga já foi aplicada."
                )

            else:

                vaga.status = "salva"

                vaga.remover_em = (
                    datetime.now(timezone.utc)
                    + timedelta(days=3)
                )

                session.commit()

                bot.answer_callback_query(
                    call.id,
                    "⭐ Vaga salva!"
                )

        elif acao == "aplicada":

            if vaga.status == "aplicada":

                bot.answer_callback_query(
                    call.id,
                    "✅ Essa vaga já foi aplicada."
                )

            else:

                vaga.status = "aplicada"

                vaga.remover_em = (
                    datetime.now(timezone.utc)
                    + timedelta(days=7)
                )

                session.commit()

                bot.answer_callback_query(
                    call.id,
                    "✅ Vaga marcada como aplicada!"
                )

        elif acao == "rejeitada":

            vaga.status = "rejeitada"

            vaga.remover_em = (
                datetime.now(timezone.utc)
                + timedelta(days=3)
            )

            if vaga.telegram_message_id:

                try:

                    bot.delete_message(
                        CANAL_ID,
                        vaga.telegram_message_id
                    )

                    vaga.telegram_message_id = None

                except ApiTelegramException as e:

                    print(
                        f"Erro ao deletar mensagem: {e}"
                    )

            session.commit()

            bot.answer_callback_query(
                call.id,
                "❌ Vaga rejeitada."
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Ação desconhecida."
            )

    except Exception:

        session.rollback()

        traceback.print_exc()

        try:

            bot.answer_callback_query(
                call.id,
                "❌ Ocorreu um erro."
            )

        except Exception:

            pass

    finally:

        session.close()


def enviar_vaga(vaga, max_tentativas=3):

    markup = quick_markup(
        {
            "✅ Aplicada": {
                "callback_data": f"aplicada:{vaga.id}"
            },
            "⭐ Salva": {
                "callback_data": f"salva:{vaga.id}"
            },
            "❌ Rejeitada": {
                "callback_data": f"rejeitada:{vaga.id}"
            },
            "🤖 Gerar análise": {
                "callback_data": f"analisar:{vaga.id}"
            }
        },
        row_width=2
    )

    for _ in range(max_tentativas):

        try:

            message = bot.send_message(
                CANAL_ID,
                vaga.mensagem,
                reply_markup=markup,
                parse_mode="HTML"
            )

            vaga.telegram_message_id = (
                message.message_id
            )

            return True

        except ApiTelegramException as e:

            if e.error_code == 429:

                retry_after = (
                    e.result_json
                    .get("parameters", {})
                    .get("retry_after", 5)
                )

                time.sleep(
                    retry_after + 1
                )

            else:

                print(
                    f"Erro ao enviar vaga {vaga.id}: {e}"
                )

                return False

        except Exception:

            traceback.print_exc()

            return False

    return False


def enviar_novas_vagas():

    session = SessionLocal()

    try:

        vagas = (
            session
            .query(Vaga)
            .filter_by(status="nova")
            .all()
        )

        for vaga in vagas:

            sucesso = enviar_vaga(
                vaga
            )

            if sucesso:

                vaga.status = "enviada"

                session.commit()

            else:

                session.rollback()

            time.sleep(1.5)

    except Exception:

        session.rollback()

        traceback.print_exc()

    finally:

        session.close()