from fastapi import APIRouter
import telebot
import os
from dotenv import load_dotenv

from app.services.telegram import bot

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

router = APIRouter()


@router.post(f"/webhook/{API_TOKEN}")
async def webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])

    return {"status": "ok"}