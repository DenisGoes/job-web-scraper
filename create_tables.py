from app.database.connection import engine
from app.database.model import Base

print("Criando tabelas...")

Base.metadata.create_all(bind=engine)

print("Tabelas criadas!")