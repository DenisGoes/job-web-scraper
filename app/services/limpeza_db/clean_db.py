from datetime import datetime, timezone

import telebot
from sqlalchemy import select
from telebot.apihelper import ApiTelegramException

from app.config.settings import API_TOKEN, CANAL_ID
from app.database.connection import SessionLocal
from app.database.model import AnaliseVaga, Vaga


if not API_TOKEN or not CANAL_ID:
    raise ValueError(
        "API_TOKEN e CANAL_ID são necessários para a limpeza do Telegram."
    )

bot = telebot.TeleBot(API_TOKEN)


def clean_dados():
    agora = datetime.now(timezone.utc)

    with SessionLocal() as session:
        try:
            vagas = session.execute(
                select(Vaga).where(
                    Vaga.remover_em.is_not(None),
                    Vaga.remover_em <= agora,
                )
            ).scalars().all()

            removidas = 0
            for vaga in vagas:
                if vaga.telegram_message_id:
                    try:
                        bot.delete_message(CANAL_ID, vaga.telegram_message_id)
                    except ApiTelegramException as e:
                        descricao = str(
                            getattr(e, "description", "")
                        ).lower()
                        if (
                            "message to delete not found" in descricao
                            or "message not found" in descricao
                        ):
                            print(
                                f"Mensagem da vaga {vaga.id} já não existe no Telegram."
                            )
                        else:
                            print(
                                f"Erro ao deletar mensagem da vaga {vaga.id}: {e}"
                            )
                            # Mantém o registro para tentar excluir a mensagem novamente.
                            continue

                session.delete(vaga)
                removidas += 1

            session.commit()

            return removidas

        except Exception:
            session.rollback()
            raise
