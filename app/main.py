from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import WEBHOOK_URL

from app.services.telegram.telegram_service import bot

from app.webhook.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("=" * 60)
    print("🚀 INICIANDO APLICAÇÃO")
    print("=" * 60)

    print(
        f"WEBHOOK_URL configurada: "
        f"{WEBHOOK_URL}"
    )

    if not WEBHOOK_URL:

        print(
            "❌ WEBHOOK_URL NÃO CONFIGURADA!"
        )

    else:

        try:

            print(
                "Configurando webhook no Telegram..."
            )

            resultado = bot.set_webhook(
                url=WEBHOOK_URL,
                allowed_updates=[
                    "callback_query"
                ]
            )

            print(
                f"Resultado set_webhook: "
                f"{resultado}"
            )

            print(
                "Webhook configurado."
            )

            print(
                "Consultando informações "
                "do webhook..."
            )

            webhook_info = (
                bot.get_webhook_info()
            )

            print(
                "WEBHOOK INFO:"
            )

            print(
                f"URL: "
                f"{webhook_info.url}"
            )

            print(
                f"Pending updates: "
                f"{webhook_info.pending_update_count}"
            )

            print(
                f"IP: "
                f"{webhook_info.ip_address}"
            )

            print(
                f"Max connections: "
                f"{webhook_info.max_connections}"
            )

            print(
                f"Last error date: "
                f"{webhook_info.last_error_date}"
            )

            print(
                f"Last error message: "
                f"{webhook_info.last_error_message}"
            )

        except Exception as e:

            print("=" * 60)
            print(
                "❌ ERRO AO CONFIGURAR WEBHOOK"
            )

            print(
                f"Tipo: {type(e).__name__}"
            )

            print(
                f"Erro: {e}"
            )

            import traceback

            traceback.print_exc()

            print("=" * 60)

    print("=" * 60)
    print("APLICAÇÃO PRONTA")
    print("=" * 60)

    yield

    print(
        "Aplicação encerrada."
    )


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