from fastapi import APIRouter, Request
import telebot

from app.services.telegram.telegram_service import bot


router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    try:
        update = await request.json()

        if not update:
            return {
                "status": "ok",
                "message": "update vazio"
            }

        telegram_update = (
            telebot.types.Update.de_json(update)
        )

        bot.process_new_updates(
            [telegram_update]
        )

        return {
            "status": "ok"
        }

    except Exception as e:
        print(f"Erro no webhook: {e}")

        return {
            "status": "error",
            "message": str(e)
        }