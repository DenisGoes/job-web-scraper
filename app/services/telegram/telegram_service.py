from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException
from app.database.connection import SessionLocal
from app.database.model import Vaga
from app.config.settings import API_TOKEN, CANAL_ID
from datetime import datetime, timedelta, timezone
import time
import traceback
import telebot
from app.services.IA.analise.analise_service import AnaliseService
import json

analise_service = AnaliseService()
bot = telebot.TeleBot(API_TOKEN)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    session = SessionLocal()

    try:
        acao, vaga_id = call.data.split(":")
        vaga_id = int(vaga_id)

        vaga = session.query(Vaga).filter_by(id=vaga_id).first()

        if not vaga:
            bot.answer_callback_query(call.id, "Vaga não encontrada.")
            return

        if acao == "salva":
            if vaga.status == "salva":
                bot.answer_callback_query(call.id, "Essa vaga já está salva.")
            elif vaga.status == "aplicada":
                bot.answer_callback_query(call.id, "Essa vaga já foi aplicada.")
            else:
                vaga.status = "salva"
                vaga.remover_em = datetime.now(timezone.utc) + timedelta(days=3)
                session.commit()
                bot.answer_callback_query(call.id, "Vaga marcada como salva")

        elif acao == "aplicada":
            if vaga.status == "aplicada":
                bot.answer_callback_query(call.id, "Essa vaga já foi aplicada.")
            else:
                vaga.status = "aplicada"
                vaga.remover_em = datetime.now(timezone.utc) + timedelta(days=7)
                session.commit()
                bot.answer_callback_query(call.id, "Vaga marcada como aplicada")

        elif acao == "rejeitada":
            if vaga.status == "rejeitada":
                bot.answer_callback_query(call.id, "Essa vaga já foi rejeitada.")
            else:
                vaga.status = "rejeitada"
                vaga.remover_em = datetime.now(timezone.utc) + timedelta(days=3)

                if vaga.telegram_message_id:
                    try:
                        bot.delete_message(CANAL_ID, vaga.telegram_message_id)
                        vaga.telegram_message_id = None  # evita nova tentativa de apagar depois
                    except ApiTelegramException as e:
                        print(f"Erro ao deletar mensagem: {e}")
                else:
                    print(
                        f"Vaga {vaga.id} não possui telegram_message_id, pulando exclusão da mensagem."
                    )

                session.commit()
                bot.answer_callback_query(call.id, "Vaga marcada como rejeitada")
        elif acao == "analisar":
            try:
                print("=" * 50)
                print("INICIANDO ANÁLISE")
                print(f"Vaga ID: {vaga.id}")
                print(f"Título: {vaga.titulo}")

                analise = analise_service.analisar(vaga)

                print("ANÁLISE RECEBIDA DO GEMINI:")
                print(analise)

                print("TIPO DA ANÁLISE:")
                print(type(analise))

                mensagem = json.dumps(
                    analise,
                    ensure_ascii=False,
                    indent=2
                )

                print("MENSAGEM QUE SERÁ ENVIADA AO TELEGRAM:")
                print(mensagem)

                print("ENVIANDO MENSAGEM...")

                bot.send_message(
                    call.message.chat.id,
                    mensagem
                )

                print("MENSAGEM ENVIADA COM SUCESSO")
                print("=" * 50)

                bot.answer_callback_query(
                    call.id,
                    "Análise gerada!"
                )

            except Exception as e:
                print("=" * 50)
                print(f"ERRO AO GERAR ANÁLISE DA VAGA {vaga.id}")
                print(f"Erro: {e}")
                traceback.print_exc()
                print("=" * 50)

                bot.answer_callback_query(
                    call.id,
                    "Erro ao gerar análise."
                )



    except Exception:
        traceback.print_exc()

    finally:
        session.close()


def enviar_vaga(vaga, max_tentativas=3):
    markup = quick_markup(
        {
            "✅ Aplicada": {"callback_data": f"aplicada:{vaga.id}"},
            "⭐ Salva": {"callback_data": f"salva:{vaga.id}"},
            "❌ Rejeitada": {"callback_data": f"rejeitada:{vaga.id}"},
            "🤖 Gerar análise": {"callback_data": f"analisar:{vaga.id}"}
        },
        row_width=2,
    )

    for tentativa in range(max_tentativas):
        try:
            message = bot.send_message(
                CANAL_ID, vaga.mensagem, reply_markup=markup, parse_mode="HTML"
            )
            vaga.telegram_message_id = message.message_id
            return True

        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result_json.get("parameters", {}).get("retry_after", 5)
                print(f"Rate limit atingido (vaga {vaga.id}). Aguardando {retry_after}s...")
                time.sleep(retry_after + 1)
            else:
                print(f"Erro ao enviar vaga {vaga.id}: {e}")
                return False

    print(f"Falha ao enviar vaga {vaga.id} após {max_tentativas} tentativas.")
    return False


def enviar_novas_vagas():
    session = SessionLocal()

    try:
        vagas = session.query(Vaga).filter_by(status="nova").all()

        print(f"{len(vagas)} vaga(s) nova(s) para enviar.")

        for vaga in vagas:
            sucesso = enviar_vaga(vaga)

            if sucesso:
                vaga.status = "enviada"
                session.commit()
            else:
                print(
                    f"Vaga {vaga.id} mantida como 'nova' para reenvio futuro."
                )
                session.rollback()

            time.sleep(1.5)

        print("Vagas enviadas!")

    except Exception as e:
        print(f"Erro envio: {e}")
        session.rollback()

    finally:
        session.close()