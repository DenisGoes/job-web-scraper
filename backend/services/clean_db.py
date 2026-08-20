from backend.database.connection import SessionLocal
from backend.database.model import Vaga
from sqlalchemy import select, or_
from datetime import datetime, timedelta, timezone

def clean_dados():
    agora = datetime.now(timezone.utc)
    with SessionLocal() as session:
        try:
            vagas = session.execute(
                select(Vaga).where(Vaga.remover_em <= agora)
            ).scalars().all()

            if vagas:
                for vaga in vagas:
                    session.delete(vaga)

                session.commit()

            return len(vagas)

        except Exception:
            session.rollback()
            raise