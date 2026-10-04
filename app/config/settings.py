import os

from dotenv import load_dotenv


# Carrega as variáveis do arquivo .env
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

INFOJOBS_LOG = os.getenv("INFOJOBS_LOG")
LINKEDIN_LOG = os.getenv("LINKEDIN_LOG")

DATABASE_URL = os.getenv("DATABASE_URL")

API_URL = os.getenv("API_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")