from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import WEBHOOK_URL
from app.services.telegram.telegram_service import bot
from app.webhook.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    if not WEBHOOK_URL:
        raise ValueError(
            "WEBHOOK_URL não configurada."
        )

    try:
        bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=[
                "callback_query"
            ]
        )

        webhook_info = bot.get_webhook_info()

        print(
            f"Webhook configurado: {webhook_info.url}"
        )

    except Exception as e:
        print(
            f"Erro ao configurar webhook: {e}"
        )

    yield


app = FastAPI(
    lifespan=lifespan
)


app.include_router(
    webhook_router
)


@app.get("/healthz")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/")
def root():
    return {
        "status": "API online"
    }