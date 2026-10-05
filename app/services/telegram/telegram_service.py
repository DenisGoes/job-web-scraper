import json
import time
import traceback

from datetime import datetime, timedelta, timezone

import telebot

from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException

from app.config.settings import API_TOKEN, CANAL_ID
from app.database.connection import SessionLocal
from app.database.model import Vaga
from app.services.IA.analise.analise_service import AnaliseService


print("=" * 60)
print("CARREGANDO TELEGRAM SERVICE")

if not API_TOKEN:
    raise ValueError("API_TOKEN não configurado.")

print("API_TOKEN encontrado.")

if not CANAL_ID:
    print("AVISO: CANAL_ID não configurado.")

analise_service = AnaliseService()

bot = telebot.TeleBot(API_TOKEN)

print("Bot Telegram criado.")
print("=" * 60)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    print("=" * 60)
    print("🔥 CALLBACK RECEBIDO PELO TELEGRAM SERVICE")

    try:
        print(f"Callback ID: {call.id}")
        print(f"Callback data: {call.data}")
        print(f"Chat ID: {call.message.chat.id if call.message else 'SEM MESSAGE'}")

    except Exception as e:
        print(f"Erro ao ler dados iniciais do callback: {e}")

    session = SessionLocal()

    try:

        print("Abrindo sessão do banco...")

        if not call.data:
            print("CALLBACK SEM DATA.")
            return

        print(f"call.data = {call.data}")

        partes = call.data.split(":")

        if len(partes) != 2:

            print(f"Formato inesperado de callback: {call.data}")

            bot.answer_callback_query(
                call.id,
                "Callback inválido."
            )

            return

        acao, vaga_id = partes

        print(f"Ação: {acao}")
        print(f"Vaga ID recebido: {vaga_id}")

        vaga_id = int(vaga_id)

        print("Buscando vaga no banco...")

        vaga = (
            session
            .query(Vaga)
            .filter_by(id=vaga_id)
            .first()
        )

        if not vaga:

            print(f"Vaga {vaga_id} não encontrada.")

            bot.answer_callback_query(
                call.id,
                "Vaga não encontrada."
            )

            return

        print(f"Vaga encontrada: {vaga.id}")
        print(f"Título: {vaga.titulo}")

        # =====================================================
        # SALVAR
        # =====================================================

        if acao == "salva":

            print("AÇÃO = SALVA")

            if vaga.status == "salva":

                bot.answer_callback_query(
                    call.id,
                    "Essa vaga já está salva."
                )

            elif vaga.status == "aplicada":

                bot.answer_callback_query(
                    call.id,
                    "Essa vaga já foi aplicada."
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
                    "Vaga marcada como salva"
                )

        # =====================================================
        # APLICADA
        # =====================================================

        elif acao == "aplicada":

            print("AÇÃO = APLICADA")

            if vaga.status == "aplicada":

                bot.answer_callback_query(
                    call.id,
                    "Essa vaga já foi aplicada."
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
                    "Vaga marcada como aplicada"
                )

        # =====================================================
        # REJEITADA
        # =====================================================

        elif acao == "rejeitada":

            print("AÇÃO = REJEITADA")

            if vaga.status == "rejeitada":

                bot.answer_callback_query(
                    call.id,
                    "Essa vaga já foi rejeitada."
                )

            else:

                vaga.status = "rejeitada"

                vaga.remover_em = (
                    datetime.now(timezone.utc)
                    + timedelta(days=3)
                )

                if vaga.telegram_message_id:

                    try:

                        print(
                            f"Deletando mensagem Telegram "
                            f"{vaga.telegram_message_id}"
                        )

                        bot.delete_message(
                            CANAL_ID,
                            vaga.telegram_message_id
                        )

                        vaga.telegram_message_id = None

                    except ApiTelegramException as e:

                        print(
                            f"Erro ao deletar mensagem: {e}"
                        )

                else:

                    print(
                        f"Vaga {vaga.id} não possui "
                        f"telegram_message_id."
                    )

                session.commit()

                bot.answer_callback_query(
                    call.id,
                    "Vaga marcada como rejeitada"
                )

        # =====================================================
        # ANALISAR
        # =====================================================

        elif acao == "analisar":

            print("=" * 60)
            print("🤖 AÇÃO = ANALISAR")
            print(f"Vaga ID: {vaga.id}")
            print(f"Título: {vaga.titulo}")
            print("Chamando AnaliseService...")

            try:

                analise = analise_service.analisar(vaga)

                print("AnaliseService retornou.")

                print("Tipo da análise:")
                print(type(analise))

                print("Conteúdo da análise:")
                print(analise)

                mensagem = json.dumps(
                    analise,
                    ensure_ascii=False,
                    indent=2
                )

                print(
                    "Tamanho da mensagem:"
                    f" {len(mensagem)} caracteres"
                )

                print(
                    "Enviando análise para o Telegram..."
                )

                chat_id = call.message.chat.id

                print(f"Chat ID destino: {chat_id}")

                resposta_telegram = bot.send_message(
                    chat_id,
                    mensagem
                )

                print(
                    "Mensagem enviada para Telegram."
                )

                print(
                    f"Message ID: "
                    f"{resposta_telegram.message_id}"
                )

                bot.answer_callback_query(
                    call.id,
                    "Análise gerada!"
                )

                print(
                    "Callback respondido com sucesso."
                )

            except Exception as e:

                print("=" * 60)
                print("❌ ERRO AO GERAR ANÁLISE")
                print(f"Tipo: {type(e).__name__}")
                print(f"Erro: {e}")

                traceback.print_exc()

                print("=" * 60)

                try:

                    bot.answer_callback_query(
                        call.id,
                        "Erro ao gerar análise."
                    )

                except Exception as callback_error:

                    print(
                        "Erro ao responder callback:"
                    )

                    print(callback_error)

        # =====================================================
        # AÇÃO DESCONHECIDA
        # =====================================================

        else:

            print(
                f"AÇÃO DESCONHECIDA: {acao}"
            )

            bot.answer_callback_query(
                call.id,
                "Ação desconhecida."
            )

    except Exception as e:

        print("=" * 60)
        print("❌ ERRO GERAL NO CALLBACK")
        print(f"Tipo: {type(e).__name__}")
        print(f"Erro: {e}")

        traceback.print_exc()

        print("=" * 60)

    finally:

        session.close()

        print("Sessão do banco fechada.")
        print("=" * 60)


def enviar_vaga(vaga, max_tentativas=3):

    print(
        f"Preparando envio da vaga {vaga.id}"
    )

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
        row_width=2,
    )

    for tentativa in range(max_tentativas):

        try:

            print(
                f"Enviando vaga {vaga.id}. "
                f"Tentativa {tentativa + 1}"
            )

            message = bot.send_message(
                CANAL_ID,
                vaga.mensagem,
                reply_markup=markup,
                parse_mode="HTML"
            )

            vaga.telegram_message_id = (
                message.message_id
            )

            print(
                f"Vaga {vaga.id} enviada. "
                f"Message ID: {message.message_id}"
            )

            return True

        except ApiTelegramException as e:

            if e.error_code == 429:

                retry_after = (
                    e.result_json
                    .get("parameters", {})
                    .get("retry_after", 5)
                )

                print(
                    f"Rate limit atingido "
                    f"(vaga {vaga.id}). "
                    f"Aguardando {retry_after}s..."
                )

                time.sleep(retry_after + 1)

            else:

                print(
                    f"Erro ao enviar vaga "
                    f"{vaga.id}: {e}"
                )

                return False

    print(
        f"Falha ao enviar vaga {vaga.id} "
        f"após {max_tentativas} tentativas."
    )

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

        print(
            f"{len(vagas)} vaga(s) nova(s) para enviar."
        )

        for vaga in vagas:

            sucesso = enviar_vaga(vaga)

            if sucesso:

                vaga.status = "enviada"

                session.commit()

            else:

                print(
                    f"Vaga {vaga.id} mantida "
                    "como 'nova' para reenvio futuro."
                )

                session.rollback()

            time.sleep(1.5)

        print("Vagas enviadas!")

    except Exception as e:

        print(f"Erro envio: {e}")

        session.rollback()

    finally:

        session.close()