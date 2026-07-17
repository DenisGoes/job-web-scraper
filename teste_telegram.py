from app.services.telegram import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


from dotenv import load_dotenv
import os

load_dotenv()

CANAL_ID = os.getenv("CANAL_ID")


markup = InlineKeyboardMarkup()

botao = InlineKeyboardButton(
    "Clique aqui",
    callback_data="teste"
)

markup.add(botao)


bot.send_message(
    CANAL_ID ,
    "Teste botão",
    reply_markup=markup
)

print("Mensagem enviada")