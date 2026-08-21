from backend.database.connection import SessionLocal
from backend.database.model import Vaga
from backend.services.telegram_client import bot, CANAL_ID
from telebot.apihelper import ApiTelegramException
from sqlalchemy import select
from datetime import datetime, timezone


def clean_dados():
    agora = datetime.now(timezone.utc)

    with SessionLocal() as session:
        try:
            vagas = session.execute(
                select(Vaga).where(Vaga.remover_em <= agora)
            ).scalars().all()

            for vaga in vagas:
                # "rejeitada" já teve a mensagem apagada no clique do botão.
                # "aplicada"/"salva" ainda estão publicadas no canal, então apaga agora.
                if vaga.telegram_message_id:
                    try:
                        bot.delete_message(CANAL_ID, vaga.telegram_message_id)
                    except ApiTelegramException as e:
                        print(f"Erro ao deletar mensagem da vaga {vaga.id}: {e}")

                session.delete(vaga)

            if vagas:
                session.commit()

            return len(vagas)

        except Exception:
            session.rollback()
            raise