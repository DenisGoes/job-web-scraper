from backend.database.connection import SessionLocal
from backend.database.model import Vaga
from sqlalchemy import select, or_
from datetime import datetime, UTC

def clean_dados():
    agora = datetime.now(UTC)
    with SessionLocal() as session:
        try:
            Vaga = session.execute(
                select(Vaga).where(Vaga.remover_em <= agora)
            ).scalars().all()

            if Vaga:
                for Vaga in Vaga:
                    session.delete(Vaga)

                session.commit()

            return len(Vaga)

        except Exception as e:
            session.rollback()
            raise