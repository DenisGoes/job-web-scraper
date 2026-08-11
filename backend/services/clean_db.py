from backend.database.connection import SessionLocal
from backend.database.model import Noticias
from sqlalchemy import select, or_
from datetime import datetime, UTC

def clean_dados():
    agora = datetime.now(UTC)
    with SessionLocal() as session:
        try:
            noticias = session.execute(
                select(Noticias).where(Noticias.remover_em <= agora)
            ).scalars().all()

            if noticias:
                for noticia in noticias:
                    session.delete(noticia)

                session.commit()

            return len(noticias)

        except Exception as e:
            session.rollback()
            raise