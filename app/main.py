from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import WEBHOOK_URL
from app.services.telegram.telegram_service import bot
from app.webhook.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("WEBHOOK:", WEBHOOK_URL)

    if WEBHOOK_URL:
        bot.set_webhook(WEBHOOK_URL)
        print("Webhook configurado")

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