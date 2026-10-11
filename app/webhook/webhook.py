from fastapi import APIRouter, Request
import telebot

from app.services.telegram.telegram_service import bot, bot_analise


router = APIRouter()


async def _processar_update(request, telegram_bot, nome):
    try:
        update = await request.json()
        if update:
            telegram_update = telebot.types.Update.de_json(update)
            telegram_bot.process_new_updates([telegram_update])
        return {"status": "ok"}
    except Exception as e:
        print(f"Erro no webhook {nome}: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/webhook")
async def webhook(request: Request):
    return await _processar_update(request, bot, "principal")


@router.post("/webhook/analise")
async def webhook_analise(request: Request):
    return await _processar_update(request, bot_analise, "de análise")
