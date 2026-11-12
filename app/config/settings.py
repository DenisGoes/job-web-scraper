import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

API_TOKEN = os.getenv("API_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

TOKEN_TELEGRAM_ANALISE = os.getenv("TOKEN_TELEGRAM_ANALISE")
CANAL_ID_ANALISE = os.getenv("CANAL_ID_ANALISE")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")