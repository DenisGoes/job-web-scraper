from backend.database.connection import SessionLocal
from backend.database.model import Vaga


def buscar_descricao_vaga(vaga_id):
    session = SessionLocal()

    try:
        vaga = session.query(Vaga).filter_by(id=vaga_id).first() #Buscar vagas no banco de dados.

        if vaga is None:
            return None

        return {
            "titulo": vaga.titulo,
            "descricao": vaga.descricao
        }
    
    except Exception as e:
        print(f"Erro! Algo inesperado aconteceu. {e}")
    finally:
        session.close()
