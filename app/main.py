from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.api.webhook import router
from app.services.telegram import bot


load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
API_URL = os.getenv("API_URL")

WEBHOOK_URL = (
    f"{API_URL}"
    f"/webhook"
)


# WEBHOOK_URL = ( # Usada em desenvolvimento e testes locais
#     f"https://dazzling-destitute-fragrance.ngrok-free.dev"
#     f"/webhook/{API_TOKEN}"
# )



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

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "API online"}