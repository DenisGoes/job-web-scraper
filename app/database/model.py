from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database.connection import Base


# Modelo que representa a tabela de vagas no banco de dados.
class Vaga(Base):

    __tablename__ = "vagas"

    id = Column(Integer, primary_key=True)

    vaga_id = Column(String, unique=True, nullable=False)
    fonte = Column(String, nullable=False)
    
    titulo = Column(String, nullable=False)
    empresa = Column(String)
    localidade = Column(String)
    salario = Column(String)
    modelo_trabalho = Column(String)
    # descricao = Column(String)
    data_publicacao = Column(String)
    link_vaga = Column(String, unique=True, nullable=False)
    mensagem = Column(Text)

    status = Column(String, default="nova")
    data_salva = Column(DateTime, nullable=True)
    data_aplicada = Column(DateTime, nullable=True)
    ultimo_lembrete = Column(DateTime, nullable=True)

    telegram_message_id = Column(Integer)

