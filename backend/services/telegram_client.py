from dotenv import load_dotenv
import telebot
import os

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

bot = telebot.TeleBot(API_TOKEN)