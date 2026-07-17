# from fastapi import FastAPI
from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException
from dotenv import load_dotenv
from app.database.connection import SessionLocal
from app.database.model import Vaga
from datetime import datetime, UTC
import os
import telebot
import time
import traceback

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

bot = telebot.TeleBot(API_TOKEN)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    print("===================================")
    print("CALLBACK RECEBIDO")
    print(call.data)
    print(call.id)
    session = SessionLocal()

    try:
        acao, vaga_id = call.data.split(":")
        vaga_id = int(vaga_id)

        vaga = session.query(Vaga).filter_by(id=vaga_id).first()

        if vaga:
            if acao == "salva":
                vaga.status = "salva"
                vaga.data_salva = datetime.now(UTC) #Registra data e hora atual
                    
                session.commit()
                bot.answer_callback_query(
                    call.id,
                    f"Vaga marcada como {acao}"
                )

            elif acao == "aplicada":
                vaga.status = "aplicada"
                vaga.data_aplicada = datetime.now(UTC) #Registra data e hora atual

                session.commit()

                bot.answer_callback_query(
                    call.id,
                    f"Vaga marcada como {acao}"
                )

            elif acao == "rejeitada":

                # Só tenta deletar a mensagem se o ID existir de fato.
                if vaga.telegram_message_id:
                    try:
                        bot.delete_message(
                            CANAL_ID,
                            vaga.telegram_message_id
                        )
                    except ApiTelegramException as e:
                        print(f"Erro ao deletar mensagem: {e}")
                else:
                    print(f"Vaga {vaga.id} não possui telegram_message_id, pulando exclusão da mensagem.")

                session.delete(vaga)
                session.commit()

                bot.answer_callback_query(call.id, "Vaga rejeitada")

    

    except Exception:
        traceback.print_exc()

    finally:
        session.close()

# Envia uma vaga para o canal do Telegram, com retry automático
# em caso de rate limit (429). Retorna True se enviou com sucesso.
def enviar_vaga(vaga, max_tentativas=3):

    markup = quick_markup({
        '✅ Aplicada': {
                'callback_data': f'aplicada:{vaga.id}'
        },
        '⭐ Salva': {
                'callback_data': f'salva:{vaga.id}'
        },
        '❌ Rejeitada': {
            'callback_data': f'rejeitada:{vaga.id}'
        }
    }, row_width=2)

    for tentativa in range(max_tentativas):
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
                retry_after = e.result_json.get("parameters", {}).get("retry_after", 5)
                print(f"Rate limit atingido (vaga {vaga.id}). Aguardando {retry_after}s...")
                time.sleep(retry_after + 1)
            else:
                print(f"Erro ao enviar vaga {vaga.id}: {e}")
                return False

    print(f"Falha ao enviar vaga {vaga.id} após {max_tentativas} tentativas.")
    return False

# Busca todas as vagas novas e as envia ao Telegram,
# uma de cada vez, respeitando o rate limit do Telegram.
def enviar_novas_vagas():

    session = SessionLocal()

    try:
        vagas = session.query(Vaga).filter_by(status="nova").all()
        print(f"{len(vagas)} vaga(s) nova(s) para enviar.")

        for vaga in vagas:
            sucesso = enviar_vaga(vaga)

            if sucesso:
                vaga.status = "enviada"
                session.commit()  # commit por vaga, evita perder tudo se algo falhar depois
            else:
                # Deixa como "nova" para tentar novamente na próxima execução.
                print(f"Vaga {vaga.id} mantida como 'nova' para reenvio futuro.")
                session.rollback()

            # Respeita o limite do Telegram para o mesmo chat (~1 msg/seg).
            time.sleep(1.5)

        print("Vagas enviadas!")

    except Exception as e:
        print(f"Erro envio: {e}")
        session.rollback()

    finally:
        session.close()
