from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import WEBHOOK_URL
from app.services.telegram.telegram_service import bot, bot_analise
from app.webhook.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL não configurada.")

    url_base = WEBHOOK_URL.rstrip("/")
    if not url_base.endswith("/webhook"):
        url_base = f"{url_base}/webhook"

    try:
        bot.set_webhook(
            url=url_base,
            allowed_updates=["callback_query", "channel_post", "message"],
        )
        bot_analise.set_webhook(
            url=f"{url_base}/analise",
            allowed_updates=["callback_query"],
        )
        print(f"Webhook principal configurado: {bot.get_webhook_info().url}", flush=True)
        print(f"Webhook análise configurado: {bot_analise.get_webhook_info().url}", flush=True)
    except Exception as e:
        print(f"Erro ao configurar webhook: {e}", flush=True)

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)


@app.api_route("/healthz", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"status": "API online"}