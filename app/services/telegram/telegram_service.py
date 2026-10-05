from datetime import datetime, timedelta, timezone
import time
import traceback

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from app.config.settings import API_TOKEN, CANAL_ID
from app.database.connection import SessionLocal
from app.database.model import Vaga
from app.services.IA.analise.analise_service import AnaliseService


print("=" * 80)
print("CARREGANDO TELEGRAM SERVICE")
print("=" * 80)

if not API_TOKEN:
    print("❌ API_TOKEN NÃO CONFIGURADO!")
    raise ValueError("API_TOKEN não configurado.")

print("✅ API_TOKEN encontrado.")

bot = telebot.TeleBot(API_TOKEN)

print("✅ Bot Telegram criado.")
print("=" * 80)


# ============================================================
# CALLBACK DEBUG
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    print("\n")
    print("=" * 80)
    print("🔥🔥🔥 CALLBACK RECEBIDO 🔥🔥🔥")
    print("=" * 80)

    try:

        print(f"Callback ID: {call.id}")
        print(f"Callback DATA: {call.data}")

        print(f"Usuário:")
        print(f"  ID: {call.from_user.id}")
        print(f"  Nome: {call.from_user.first_name}")
        print(f"  Username: {call.from_user.username}")

        if call.message:

            print("Mensagem:")
            print(f"  Message ID: {call.message.message_id}")

            if call.message.chat:
                print(f"  Chat ID: {call.message.chat.id}")
                print(f"  Chat TYPE: {call.message.chat.type}")
                print(f"  Chat TITLE: {call.message.chat.title}")

        else:

            print("⚠️ call.message é None")

        print("-" * 80)
        print("TESTANDO answer_callback_query...")

        bot.answer_callback_query(
            callback_query_id=call.id,
            text="✅ Callback recebido pelo servidor!"
        )

        print("✅ answer_callback_query FUNCIONOU")

        print("-" * 80)

        # --------------------------------------------------------
        # NÃO FAZER BANCO
        # NÃO FAZER GEMINI
        # NÃO FAZER OUTRAS OPERAÇÕES
        # --------------------------------------------------------

        print("✅ CALLBACK DEBUG FINALIZADO")
        print("=" * 80)

    except Exception as e:

        print("=" * 80)
        print("❌ ERRO DENTRO DO CALLBACK")
        print("=" * 80)

        print(f"Tipo do erro: {type(e).__name__}")
        print(f"Mensagem: {e}")

        traceback.print_exc()

        print("=" * 80)


# ============================================================
# ENVIO DE VAGA
# ============================================================

def enviar_vaga(vaga, max_tentativas=3):

    print("=" * 80)
    print(f"ENVIANDO VAGA {vaga.id}")
    print("=" * 80)

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

    print("Callback buttons criados:")
    print(f"  aplicada:{vaga.id}")
    print(f"  salva:{vaga.id}")
    print(f"  rejeitada:{vaga.id}")
    print(f"  analisar:{vaga.id}")

    for tentativa in range(max_tentativas):

        try:

            print(
                f"Tentativa {tentativa + 1}/{max_tentativas} "
                f"para enviar vaga {vaga.id}"
            )

            message = bot.send_message(
                CANAL_ID,
                vaga.mensagem,
                reply_markup=markup,
                parse_mode="HTML"
            )

            print(
                f"✅ Vaga enviada. "
                f"Telegram message_id={message.message_id}"
            )

            vaga.telegram_message_id = message.message_id

            return True

        except ApiTelegramException as e:

            print("=" * 80)
            print("❌ ERRO TELEGRAM AO ENVIAR VAGA")
            print("=" * 80)

            print(f"Status code: {e.error_code}")
            print(f"Erro: {e}")

            if e.error_code == 429:

                retry_after = (
                    e.result_json
                    .get("parameters", {})
                    .get("retry_after", 5)
                )

                print(
                    f"Rate limit. "
                    f"Aguardando {retry_after}s..."
                )

                time.sleep(retry_after + 1)

            else:

                return False

        except Exception as e:

            print("=" * 80)
            print("❌ ERRO INESPERADO AO ENVIAR VAGA")
            print("=" * 80)

            print(f"Tipo: {type(e).__name__}")
            print(f"Erro: {e}")

            traceback.print_exc()

            return False

    print(
        f"❌ Falha ao enviar vaga {vaga.id} "
        f"após {max_tentativas} tentativas."
    )

    return False


# ============================================================
# ENVIO DE NOVAS VAGAS
# ============================================================

def enviar_novas_vagas():

    print("=" * 80)
    print("PROCURANDO NOVAS VAGAS")
    print("=" * 80)

    session = SessionLocal()

    try:

        vagas = (
            session
            .query(Vaga)
            .filter_by(status="nova")
            .all()
        )

        print(
            f"{len(vagas)} vaga(s) nova(s) "
            f"encontrada(s)."
        )

        for vaga in vagas:

            print("-" * 80)
            print(f"Processando vaga ID: {vaga.id}")

            sucesso = enviar_vaga(vaga)

            if sucesso:

                vaga.status = "enviada"

                session.commit()

                print(
                    f"✅ Vaga {vaga.id} marcada como enviada."
                )

            else:

                print(
                    f"⚠️ Vaga {vaga.id} continuará como nova."
                )

                session.rollback()

            time.sleep(1.5)

        print("✅ Processo de envio finalizado.")

    except Exception as e:

        print("=" * 80)
        print("❌ ERRO AO ENVIAR NOVAS VAGAS")
        print("=" * 80)

        print(f"Tipo: {type(e).__name__}")
        print(f"Erro: {e}")

        traceback.print_exc()

        session.rollback()

    finally:

        session.close()

        print("Sessão do banco fechada.")


# ============================================================
# FUNÇÕES AUXILIARES ANTIGAS
# ============================================================

def marcar_salva(vaga):

    vaga.status = "salva"

    vaga.remover_em = (
        datetime.now(timezone.utc)
        + timedelta(days=3)
    )


def marcar_aplicada(vaga):

    vaga.status = "aplicada"

    vaga.remover_em = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    )


def marcar_rejeitada(vaga):

    vaga.status = "rejeitada"

    vaga.remover_em = (
        datetime.now(timezone.utc)
        + timedelta(days=3)
    )


print("=" * 80)
print("✅ TELEGRAM SERVICE CARREGADO")
print("✅ CALLBACK DEBUG ATIVO")
print("⚠️ GEMINI NÃO SERÁ EXECUTADO NESTE TESTE")
print("⚠️ BANCO NÃO SERÁ CONSULTADO PELO CALLBACK")
print("=" * 80)