from backend.database.connection import SessionLocal
from backend.database.model import Vaga
from sqlalchemy import select, or_
from datetime import datetime, UTC

def clean_dados():
    agora = datetime.now(UTC)
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