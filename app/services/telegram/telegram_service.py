from datetime import datetime, timedelta, timezone
import json
import time
import traceback

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from app.config.settings import API_TOKEN, CANAL_ID
from app.database.connection import SessionLocal
from app.database.model import Vaga
from app.services.IA.analise.analise_service import AnaliseService


if not API_TOKEN:
    raise ValueError("API_TOKEN não configurado.")

analise_service = AnaliseService()

bot = telebot.TeleBot(API_TOKEN)


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
                analise = analise_service.analisar(vaga)

                mensagem = json.dumps(
                    analise,
                    ensure_ascii=False,
                    indent=2
                )

                limite = 4000

                partes = [
                    mensagem[i:i + limite]
                    for i in range(0, len(mensagem), limite)
                ]

                for parte in partes:
                    bot.send_message(
                        call.message.chat.id,
                        parte
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

            vaga.telegram_message_id = message.message_id

            return True

        except ApiTelegramException as e:

            if e.error_code == 429:

                retry_after = (
                    e.result_json
                    .get("parameters", {})
                    .get("retry_after", 5)
                )

                time.sleep(retry_after + 1)

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

            sucesso = enviar_vaga(vaga)

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