from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.api.webhook import router as webhook_router
from app.services.telegram import bot


load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):

    # configura webhook ao iniciar
    if WEBHOOK_URL:
        bot.set_webhook(
            url=WEBHOOK_URL
        )
        print(f"Webhook configurado: {WEBHOOK_URL}")

    yield

    print("Aplicação encerrada")


app = FastAPI(
    lifespan=lifespan
)


app.include_router(webhook_router)

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "API online"}
# WEBHOOK_URL = ( # Usada em desenvolvimento e testes locais
#     f"https://dazzling-destitute-fragrance.ngrok-free.dev"
#     f"/webhook/{API_TOKEN}"
# )