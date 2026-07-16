from app.database.connection import SessionLocal
from app.database.model import Vaga


# Salva uma nova vaga no banco de dados.
# Antes de inserir, verifica se já existe uma vaga com o mesmo ID.
def salvar_vaga(
    vaga_id,
    fonte,
    titulo,
    empresa,
    localidade,
    link_vaga,
    data_publicacao,
    mensagem
):
    # Cria uma sessão para realizar operações no banco de dados.
    session = SessionLocal()

    try:
        # Busca uma vaga com o mesmo ID para evitar duplicidade.
        vaga_existente = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        if vaga_existente:
            print("Vaga já existe no banco de dados.")
            return False

        # Cria uma nova instância do modelo Vaga.
        nova_vaga = Vaga(
            vaga_id=vaga_id,
            fonte=fonte,
            titulo=titulo,
            empresa=empresa,
            localidade=localidade,
            link_vaga=link_vaga,
            data_publicacao=data_publicacao,
            mensagem=mensagem
        )

        # Adiciona a vaga e confirma a transação.
        session.add(nova_vaga)
        session.commit()

        print("Vaga salva com sucesso!")
        return True

    except Exception as e:
        # Desfaz a transação caso ocorra algum erro.
        session.rollback()

        print(f"Erro ao salvar vaga: {e}")
        return False

    finally:
        # Encerra a sessão com o banco de dados.
        session.close()


# Retorna todas as vagas cadastradas.
def buscar_todas_vagas():
    session = SessionLocal()

    try:
        return session.query(Vaga).all()

    except Exception as e:
        print(f"Erro ao buscar vagas: {e}")
        return []

    finally:
        session.close()


# Busca uma vaga específica pelo seu ID.
def buscar_vaga_por_id(vaga_id):
    session = SessionLocal()

    try:
        return session.query(Vaga).filter_by(vaga_id=vaga_id).first()

    except Exception as e:
        print(f"Erro ao buscar a vaga: {e}")
        return False

    finally:
        session.close()


# Atualiza o status de uma vaga existente.
def atualizar_status(vaga_id, novo_status):
    session = SessionLocal()

    try:
        # Localiza a vaga que será atualizada.
        vaga = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        if not vaga:
            return "Vaga não encontrada."

        # Atualiza o status e salva a alteração.
        vaga.status = novo_status
        session.commit()

        return "Status atualizado com sucesso!"

    except Exception as e:
        session.rollback()

        print(f"Erro ao atualizar status: {e}")
        return False

    finally:
        session.close()


# Remove uma vaga do banco de dados.
def deletar_vaga(vaga_id):
    session = SessionLocal()

    try:
        # Busca a vaga antes de realizar a exclusão.
        vaga = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        if not vaga:
            return "Vaga não encontrada."

        # Remove a vaga e confirma a transação.
        session.delete(vaga)
        session.commit()

        return "Vaga deletada com sucesso!"

    except Exception as e:
        session.rollback()

        print(f"Erro: não foi possível deletar a vaga: {e}")
        return False

    finally:
        session.close()