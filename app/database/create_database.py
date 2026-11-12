from sqlalchemy import inspect

from app.database.connection import engine
from app.database.model import Base


def criar_banco() -> None:
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    print(f"Banco inicializado com sucesso! Tabelas disponíveis: {', '.join(tabelas)}")


if __name__ == "__main__":
    criar_banco()