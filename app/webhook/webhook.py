from fastapi import APIRouter, Request

import telebot

from app.services.telegram.telegram_service import bot


router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    print("=" * 60)
    print("🔥🔥🔥 WEBHOOK RECEBEU UMA REQUISIÇÃO 🔥🔥🔥")

    try:

        update = await request.json()

        print("UPDATE RECEBIDO DO TELEGRAM:")
        print(update)

        print(
            f"Tipo do update: {type(update)}"
        )

        if not update:

            print("UPDATE VAZIO.")

            return {
                "status": "ok",
                "message": "update vazio"
            }

        print(
            "Convertendo update para "
            "telebot.types.Update..."
        )

        telegram_update = (
            telebot.types.Update.de_json(update)
        )

        print(
            "Update convertido com sucesso."
        )

        print(
            "Enviando update para "
            "bot.process_new_updates()..."
        )

        bot.process_new_updates(
            [telegram_update]
        )

        print(
            "bot.process_new_updates() executado."
        )

        print("=" * 60)

        return {
            "status": "ok"
        }

    except Exception as e:

        print("=" * 60)
        print("❌ ERRO NO WEBHOOK")
        print(f"Tipo: {type(e).__name__}")
        print(f"Erro: {e}")

        import traceback

        traceback.print_exc()

        print("=" * 60)

        return {
            "status": "error",
            "message": str(e)
        }