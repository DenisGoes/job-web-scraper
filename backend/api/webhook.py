from fastapi import APIRouter
import telebot
import os

from backend.services.telegram import bot


router = APIRouter()

API_TOKEN = os.getenv("API_TOKEN")


# PRODUÇÃO
@router.post("/webhook")
async def webhook(update: dict):

    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])

    return {"status": "ok"}



# DESENVOLVIMENTO LOCAL

# Webhook usado com ngrok
# https://xxxxx.ngrok-free.dev/webhook/dev/TOKEN
# @router.post("/webhook/dev/{token}")
# async def webhook_dev(token: str, update: dict):

#     if token != API_TOKEN:
#         return {
#             "status": "error",
#             "message": "token inválido"
#         }

#     if update:
#         update = telebot.types.Update.de_json(update)
#         bot.process_new_updates([update])

#     return {"status": "ok"}