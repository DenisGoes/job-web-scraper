from fastapi import APIRouter
import telebot
from app.services.telegram import bot

router = APIRouter()


@router.post("/webhook")
async def webhook(update: dict):

    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])

    return {"status": "ok"}