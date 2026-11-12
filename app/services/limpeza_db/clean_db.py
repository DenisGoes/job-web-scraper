from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
import telebot
from sqlalchemy import delete, func, select
from telebot.apihelper import ApiTelegramException

from app.database.connection import SessionLocal
from app.database.model import AnaliseVaga, Vaga

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

if not API_TOKEN or not CANAL_ID:
    raise ValueError(
        "API_TOKEN e CANAL_ID são necessários para a limpeza do Telegram."
    )

bot = telebot.TeleBot(API_TOKEN)

ERROS_TELEGRAM_IGNORAVEIS = (
    "message to delete not found",
    "message not found",
    "message can't be deleted",
    "message identifier is not specified",
)

PRAZO_POR_STATUS_DIAS = {
    "enviada": 5,
    "salva": 5,
    "aplicada": 8,
}


def _garantir_utc(dt: datetime | None) -> datetime | None:
    """Garante comparação segura entre timestamps com e sem timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def deve_remover_vaga(vaga: Vaga, agora: datetime) -> tuple[bool, str]:
    status = (vaga.status or "enviada").strip().lower()

    # 1. Exclusão instantânea
    if status in ("excluida", "rejeitada"):
        return True, f"status '{status}' (remoção imediata)"

    # 2. Se remover_em já foi gravado no banco e venceu
    remover_em = _garantir_utc(vaga.remover_em)
    if remover_em and remover_em <= agora:
        return True, f"prazo remover_em vencido ({remover_em.isoformat()})"

    # 3. Verificação pelos timestamps de cada status
    prazo_dias = PRAZO_POR_STATUS_DIAS.get(status)
    if prazo_dias is None:
        return False, ""

    if status == "aplicada":
        data_base = _garantir_utc(vaga.data_aplicada or vaga.atualizado_em or vaga.criado_em)
    elif status == "salva":
        data_base = _garantir_utc(vaga.data_salva or vaga.atualizado_em or vaga.criado_em)
    else:
        data_base = _garantir_utc(vaga.atualizado_em or vaga.criado_em)

    if data_base and (agora - data_base) >= timedelta(days=prazo_dias):
        return True, f"status '{status}' excedeu {prazo_dias} dias desde {data_base.isoformat()}"

    return False, ""


def _deletar_mensagem_telegram(vaga: Vaga) -> bool:
    if not vaga.telegram_message_id:
        return True

    try:
        bot.delete_message(CANAL_ID, vaga.telegram_message_id)
        return True
    except ApiTelegramException as e:
        descricao = str(getattr(e, "description", "") or e).lower()
        if any(err in descricao for err in ERROS_TELEGRAM_IGNORAVEIS):
            print(
                f"Aviso Telegram (vaga ID={vaga.id}): '{descricao}'. "
                "Prosseguindo com a remoção no banco."
            )
            return True

        print(f"Erro temporário ao deletar mensagem da vaga ID={vaga.id}: {e}")
        return False
    except Exception as e:
        print(f"Falha inesperada ao contatar Telegram para vaga ID={vaga.id}: {e}")
        return False


def clean_dados() -> int:
    agora = datetime.now(timezone.utc)

    with SessionLocal() as session:
        try:
            total_antes = session.scalar(select(func.count()).select_from(Vaga)) or 0
            todas_vagas = session.execute(select(Vaga)).scalars().all()

            candidatas: list[tuple[Vaga, str]] = []
            atualizadas_prazo = 0

            for vaga in todas_vagas:
                status = (vaga.status or "enviada").strip().lower()

                if vaga.remover_em is None and status in PRAZO_POR_STATUS_DIAS:
                    vaga.remover_em = agora + timedelta(days=PRAZO_POR_STATUS_DIAS[status])
                    atualizadas_prazo += 1
                    continue

                remover, motivo = deve_remover_vaga(vaga, agora)
                if remover:
                    candidatas.append((vaga, motivo))

            print(
                f"[{agora.isoformat()}] Vagas no banco: {total_antes} | "
                f"Elegíveis para remoção: {len(candidatas)} | "
                f"Prazos normalizados: {atualizadas_prazo}"
            )

            removidas = 0
            for vaga, motivo in candidatas:
                if not _deletar_mensagem_telegram(vaga):
                    continue

                print(f"Removendo vaga ID={vaga.id} ('{vaga.titulo}') -> {motivo}")

                session.execute(
                    delete(AnaliseVaga).where(AnaliseVaga.vaga_id == vaga.id)
                )
                session.delete(vaga)
                removidas += 1

            session.commit()

            total_depois = session.scalar(select(func.count()).select_from(Vaga)) or 0
            print(
                f"Limpeza concluída: {removidas} vaga(s) removida(s) | "
                f"Restantes no banco: {total_depois}"
            )
            return removidas

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    clean_dados()