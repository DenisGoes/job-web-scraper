from datetime import datetime, timedelta, timezone
import json
from typing import Any, Optional

from sqlalchemy import or_, select

from app.database.connection import SessionLocal
from app.database.model import AnaliseVaga, Vaga


def calcular_remover_em(status: str, base: datetime | None = None) -> datetime:
    agora = base or datetime.now(timezone.utc)
    status_norm = (status or "enviada").strip().lower()

    if status_norm in ("excluida", "rejeitada"):
        return agora
    if status_norm == "aplicada":
        return agora + timedelta(days=8)
    # 'enviada' ou 'salva'
    return agora + timedelta(days=5)


def salvar_vaga(
    vaga_id: str,
    fonte: str,
    titulo: str,
    link_vaga: str,
    empresa: Optional[str] = None,
    localidade: Optional[str] = None,
    salario: Optional[str] = None,
    modelo_trabalho: Optional[str] = None,
    descricao: Optional[str] = None,
    data_publicacao: Optional[str] = None,
    mensagem: Optional[str] = None,
    remover_em: Optional[datetime] = None,
) -> bool:
    with SessionLocal() as session:
        try:
            stmt = select(Vaga).where(
                or_(Vaga.vaga_id == vaga_id, Vaga.link_vaga == link_vaga)
            )
            if session.scalar(stmt):
                print("Vaga já existe no banco de dados.")
                return False

            nova_vaga = Vaga(
                vaga_id=vaga_id,
                fonte=fonte,
                titulo=titulo,
                empresa=empresa,
                localidade=localidade,
                salario=salario,
                modelo_trabalho=modelo_trabalho,
                descricao=descricao,
                link_vaga=link_vaga,
                data_publicacao=data_publicacao,
                mensagem=mensagem,
                remover_em=remover_em,
            )

            session.add(nova_vaga)
            session.commit()

            print("Vaga salva com sucesso!")
            return True

        except Exception as e:
            session.rollback()
            print(f"Erro ao salvar vaga: {e}")
            return False


def buscar_todas_vagas() -> list[Vaga]:
    with SessionLocal() as session:
        try:
            return list(session.scalars(select(Vaga)).all())
        except Exception as e:
            print(f"Erro ao buscar vagas: {e}")
            return []


def buscar_vaga_por_id(vaga_id: str) -> Optional[Vaga]:
    with SessionLocal() as session:
        try:
            return session.scalar(select(Vaga).where(Vaga.vaga_id == vaga_id))
        except Exception as e:
            print(f"Erro ao buscar a vaga: {e}")
            return None


def atualizar_status(vaga_id: str, novo_status: str) -> str | bool:
    status_norm = novo_status.strip().lower()
    agora = datetime.now(timezone.utc)

    with SessionLocal() as session:
        try:
            vaga = session.scalar(select(Vaga).where(Vaga.vaga_id == vaga_id))
            if not vaga:
                return "Vaga não encontrada."

            if status_norm in ("excluida", "rejeitada"):
                session.delete(vaga)
                session.commit()
                return "Vaga excluída com sucesso!"

            vaga.status = status_norm
            vaga.remover_em = calcular_remover_em(status_norm, base=agora)

            if status_norm == "salva":
                vaga.data_salva = agora
            elif status_norm == "aplicada":
                vaga.data_aplicada = agora

            session.commit()
            return "Status atualizado com sucesso!"

        except Exception as e:
            session.rollback()
            print(f"Erro ao atualizar status: {e}")
            return False


def deletar_vaga(vaga_id: str) -> str | bool:
    with SessionLocal() as session:
        try:
            vaga = session.scalar(select(Vaga).where(Vaga.vaga_id == vaga_id))
            if not vaga:
                return "Vaga não encontrada."

            session.delete(vaga)
            session.commit()
            return "Vaga deletada com sucesso!"

        except Exception as e:
            session.rollback()
            print(f"Erro: não foi possível deletar a vaga: {e}")
            return False



def salvar_analise_vaga(vaga_pk_id: int, resultado_json: dict[str, Any] | str) -> bool:
    conteudo = (
        resultado_json
        if isinstance(resultado_json, str)
        else json.dumps(resultado_json, ensure_ascii=False)
    )
    with SessionLocal() as session:
        try:
            registro = session.scalar(
                select(AnaliseVaga).where(AnaliseVaga.vaga_id == vaga_pk_id)
            )
            if registro is None:
                registro = AnaliseVaga(vaga_id=vaga_pk_id, resultado_json=conteudo)
                session.add(registro)
            else:
                registro.resultado_json = conteudo

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Erro ao salvar análise da vaga: {e}")
            return False


def buscar_analises_por_vaga(vaga_pk_id: int) -> list[AnaliseVaga]:
    with SessionLocal() as session:
        try:
            stmt = select(AnaliseVaga).where(AnaliseVaga.vaga_id == vaga_pk_id)
            return list(session.scalars(stmt).all())
        except Exception as e:
            print(f"Erro ao buscar análises: {e}")
            return []