from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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
    descricao = Column(String)
    data_publicacao = Column(String)
    link_vaga = Column(String, unique=True, nullable=False)
    mensagem = Column(Text)

    status = Column(String, default="nova")
    remover_em = Column(DateTime(timezone=True), nullable=True)
    ultimo_lembrete = Column(DateTime(timezone=True), nullable=True)
    telegram_message_id = Column(Integer)
    analise = relationship(
        "AnaliseVaga",
        back_populates="vaga",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AnaliseVaga(Base):

    __tablename__ = "analises_vagas"

    id = Column(Integer, primary_key=True)
    vaga_id = Column(Integer, ForeignKey("vagas.id"), nullable=False, unique=True)
    resultado_json = Column(Text, nullable=False)
    vaga = relationship("Vaga", back_populates="analise")

