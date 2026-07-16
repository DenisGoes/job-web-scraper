from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.api.webhook import router
from app.services.telegram import bot


load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

WEBHOOK_URL = (
    f"https://dazzling-destitute-fragrance.ngrok-free.dev"
    f"/webhook/{API_TOKEN}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Executa quando o servidor inicia
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    print("Webhook configurado!")

    yield  # Aqui o FastAPI fica rodando

    # Executa quando o servidor é encerrado
    bot.remove_webhook()

    print("Webhook removido!")


app = FastAPI(lifespan=lifespan)

app.include_router(router)