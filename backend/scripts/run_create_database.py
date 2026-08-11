from backend.database.connection import Base, engine
from backend.database.model import Vaga
Base.metadata.create_all(bind=engine)

print("Banco e tabelas criados com sucesso!")