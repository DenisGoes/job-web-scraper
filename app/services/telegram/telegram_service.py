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


print("=" * 80)
print("CARREGANDO TELEGRAM SERVICE")
print("=" * 80)

if not API_TOKEN:
    print("❌ API_TOKEN NÃO CONFIGURADO!")
    raise ValueError("API_TOKEN não configurado.")

print("✅ API_TOKEN encontrado.")

analise_service = AnaliseService()

print("✅ AnaliseService criado.")

bot = telebot.TeleBot(API_TOKEN)

print("✅ Bot Telegram criado.")
print("=" * 80)


# ============================================================
# CALLBACK
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    print("\n")
    print("=" * 80)
    print("🔥 CALLBACK RECEBIDO")
    print("=" * 80)

    print(f"Callback ID: {call.id}")
    print(f"Callback DATA: {call.data}")

    if call.message:
        print(f"Message ID: {call.message.message_id}")
        print(f"Chat ID: {call.message.chat.id}")

    # --------------------------------------------------------
    # RESPONDE IMEDIATAMENTE AO TELEGRAM
    # --------------------------------------------------------

    try:

        bot.answer_callback_query(
            call.id,
            "⏳ Processando..."
        )

        print("✅ Callback respondido ao Telegram.")

    except Exception as e:

        print("❌ Erro no answer_callback_query:")
        print(type(e).__name__)
        print(e)

    # --------------------------------------------------------
    # ABRE BANCO
    # --------------------------------------------------------

    session = SessionLocal()

    try:

        print("-" * 80)
        print("ABRINDO SESSÃO DO BANCO")

        # ----------------------------------------------------
        # INTERPRETA CALLBACK
        # ----------------------------------------------------

        try:

            acao, vaga_id = call.data.split(":")

            vaga_id = int(vaga_id)

            print(f"Ação: {acao}")
            print(f"Vaga ID: {vaga_id}")

        except Exception as e:

            print("❌ ERRO AO INTERPRETAR CALLBACK")
            print(f"Callback recebido: {call.data}")
            print(type(e).__name__)
            print(e)

            return

        # ----------------------------------------------------
        # BUSCA VAGA
        # ----------------------------------------------------

        print("-" * 80)
        print("BUSCANDO VAGA NO BANCO")

        vaga = (
            session
            .query(Vaga)
            .filter_by(id=vaga_id)
            .first()
        )

        if not vaga:

            print(f"❌ VAGA {vaga_id} NÃO ENCONTRADA")

            return

        print("✅ VAGA ENCONTRADA")

        print(f"ID: {vaga.id}")
        print(f"Título: {vaga.titulo}")
        print(f"Empresa: {vaga.empresa}")
        print(f"Localidade: {vaga.localidade}")
        print(f"Status: {vaga.status}")

        # ====================================================
        # ANALISAR
        # ====================================================

        if acao == "analisar":

            print("=" * 80)
            print("🤖 INICIANDO ANÁLISE")
            print("=" * 80)

            try:

                print("Chamando AnaliseService.analisar()...")

                analise = analise_service.analisar(vaga)

                print("✅ GEMINI RETORNOU")

                print(f"Tipo da resposta: {type(analise)}")

                print("Resultado:")

                print(
                    json.dumps(
                        analise,
                        ensure_ascii=False,
                        indent=2
                    )
                )

                # ------------------------------------------------
                # PREPARA MENSAGEM
                # ------------------------------------------------

                mensagem = json.dumps(
                    analise,
                    ensure_ascii=False,
                    indent=2
                )

                print("-" * 80)
                print("TAMANHO DA MENSAGEM")
                print(len(mensagem))

                # ------------------------------------------------
                # TELEGRAM LIMITA MENSAGENS
                # ------------------------------------------------

                if len(mensagem) > 4000:

                    print(
                        "⚠️ Mensagem maior que 4000 caracteres."
                    )

                    partes = [
                        mensagem[i:i + 4000]
                        for i in range(
                            0,
                            len(mensagem),
                            4000
                        )
                    ]

                else:

                    partes = [mensagem]

                # ------------------------------------------------
                # ENVIA PARA TELEGRAM
                # ------------------------------------------------

                print("=" * 80)
                print("📤 ENVIANDO ANÁLISE PARA TELEGRAM")
                print("=" * 80)

                for i, parte in enumerate(partes, start=1):

                    print(
                        f"Enviando parte {i}/{len(partes)}"
                    )

                    resultado = bot.send_message(
                        call.message.chat.id,
                        parte
                    )

                    print(
                        f"✅ Parte {i} enviada."
                    )

                    print(
                        f"Message ID: {resultado.message_id}"
                    )

                print("=" * 80)
                print("🎉 ANÁLISE ENVIADA COM SUCESSO")
                print("=" * 80)

            except Exception as e:

                print("=" * 80)
                print("❌ ERRO AO GERAR/ENVIAR ANÁLISE")
                print("=" * 80)

                print(f"Tipo: {type(e).__name__}")
                print(f"Erro: {e}")

                traceback.print_exc()

                print("=" * 80)

                try:

                    bot.send_message(
                        call.message.chat.id,
                        "❌ Ocorreu um erro ao gerar a análise."
                    )

                except Exception as telegram_error:

                    print(
                        "❌ Também falhou ao enviar mensagem de erro:"
                    )

                    print(telegram_error)

        # ====================================================
        # SALVA
        # ====================================================

        elif acao == "salva":

            print("⭐ AÇÃO: SALVAR")

            if vaga.status == "salva":

                bot.send_message(
                    call.message.chat.id,
                    "Essa vaga já está salva."
                )

            elif vaga.status == "aplicada":

                bot.send_message(
                    call.message.chat.id,
                    "Essa vaga já foi aplicada."
                )

            else:

                vaga.status = "salva"

                vaga.remover_em = (
                    datetime.now(timezone.utc)
                    + timedelta(days=3)
                )

                session.commit()

                bot.send_message(
                    call.message.chat.id,
                    "⭐ Vaga marcada como salva."
                )

        # ====================================================
        # APLICADA
        # ====================================================

        elif acao == "aplicada":

            print("✅ AÇÃO: APLICADA")

            if vaga.status == "aplicada":

                bot.send_message(
                    call.message.chat.id,
                    "Essa vaga já foi aplicada."
                )

            else:

                vaga.status = "aplicada"

                vaga.remover_em = (
                    datetime.now(timezone.utc)
                    + timedelta(days=7)
                )

                session.commit()

                bot.send_message(
                    call.message.chat.id,
                    "✅ Vaga marcada como aplicada."
                )

        # ====================================================
        # REJEITADA
        # ====================================================

        elif acao == "rejeitada":

            print("❌ AÇÃO: REJEITADA")

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

                    print(
                        "Mensagem da vaga removida do Telegram."
                    )

                except ApiTelegramException as e:

                    print(
                        f"Erro ao deletar mensagem: {e}"
                    )

            session.commit()

            print(
                f"Vaga {vaga.id} marcada como rejeitada."
            )

    except Exception as e:

        print("=" * 80)
        print("❌ ERRO GERAL NO CALLBACK")
        print("=" * 80)

        print(f"Tipo: {type(e).__name__}")
        print(f"Erro: {e}")

        traceback.print_exc()

        print("=" * 80)

    finally:

        session.close()

        print("Sessão do banco fechada.")

        print("=" * 80)
        print("CALLBACK FINALIZADO")
        print("=" * 80)


# ============================================================
# ENVIAR VAGA
# ============================================================

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
        row_width=2,
    )

    for tentativa in range(max_tentativas):

        try:

            print(
                f"Enviando vaga {vaga.id}..."
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
                f"✅ Vaga {vaga.id} enviada."
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
                    f"Rate limit. "
                    f"Aguardando {retry_after}s..."
                )

                time.sleep(
                    retry_after + 1
                )

            else:

                print(
                    f"❌ Erro ao enviar vaga "
                    f"{vaga.id}: {e}"
                )

                return False

        except Exception as e:

            print(
                f"❌ Erro inesperado "
                f"ao enviar vaga {vaga.id}: {e}"
            )

            traceback.print_exc()

            return False

    return False


# ============================================================
# ENVIAR NOVAS VAGAS
# ============================================================

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

                session.rollback()

            time.sleep(1.5)

    except Exception as e:

        print(
            f"Erro envio: {e}"
        )

        traceback.print_exc()

        session.rollback()

    finally:

        session.close()