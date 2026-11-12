from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Vaga(Base):
    __tablename__ = "vagas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    vaga_id: Mapped[str] = mapped_column(String, unique=True)
    fonte: Mapped[str] = mapped_column(String)

    titulo: Mapped[str] = mapped_column(String)
    empresa: Mapped[Optional[str]] = mapped_column(String)
    localidade: Mapped[Optional[str]] = mapped_column(String)
    salario: Mapped[Optional[str]] = mapped_column(String)
    modelo_trabalho: Mapped[Optional[str]] = mapped_column(String)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    data_publicacao: Mapped[Optional[str]] = mapped_column(String)
    link_vaga: Mapped[str] = mapped_column(String, unique=True)
    mensagem: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String, default="nova")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    data_salva: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    data_aplicada: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ultimo_lembrete: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    remover_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer)

    analises: Mapped[list["AnaliseVaga"]] = relationship(
        back_populates="vaga",
        cascade="all, delete-orphan",
    )


class AnaliseVaga(Base):
    __tablename__ = "analises_vagas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vaga_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vagas.id", ondelete="CASCADE"),
        unique=True,
    )
    resultado_json: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    vaga: Mapped["Vaga"] = relationship(back_populates="analises")