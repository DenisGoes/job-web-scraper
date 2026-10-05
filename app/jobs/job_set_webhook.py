from app.services.telegram.telegram_service import bot
from app.config.settings import WEBHOOK_URL



bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

print(f"WebHook configurado: {WEBHOOK_URL}")