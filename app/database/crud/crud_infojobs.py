from app.database.connection import SessionLocal
from app.database.model import Vaga


# Salva uma nova vaga no banco de dados.
# Antes de inserir, verifica se já existe uma vaga com o mesmo ID,
# evitando registros duplicados.
def salvar_vaga(
    vaga_id,
    fonte,
    titulo,
    empresa,
    localidade,
    salario,
    modelo_trabalho,
    link_vaga,
    data_publicacao,
    mensagem,
):
    # Cria uma nova sessão de conexão com o banco de dados.
    session = SessionLocal()

    try:
        # Verifica se a vaga já está cadastrada no banco.
        vaga_existente = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        if vaga_existente:
            print("Vaga já existe no banco de dados.")
            return False

        # Cria um novo objeto Vaga com os dados recebidos.
        nova_vaga = Vaga(
            vaga_id=vaga_id,
            fonte=fonte,
            titulo=titulo,
            empresa=empresa,
            localidade=localidade,
            salario=salario,
            modelo_trabalho=modelo_trabalho,
            link_vaga=link_vaga,
            data_publicacao=data_publicacao,
            mensagem=mensagem
        )

        # Adiciona a vaga à sessão e confirma a transação.
        session.add(nova_vaga)
        session.commit()

        print("Vaga salva com sucesso!")
        return True

    except Exception as e:
        # Desfaz qualquer alteração caso ocorra um erro.
        session.rollback()

        print(f"Erro ao salvar vaga: {e}")
        return False

    finally:
        # Fecha a sessão, liberando os recursos utilizados.
        session.close()


# Retorna todas as vagas cadastradas no banco de dados.
def buscar_todas_vagas():
    session = SessionLocal()

    try:
        # Recupera todos os registros da tabela de vagas.
        vagas = session.query(Vaga).all()
        return vagas

    except Exception as e:
        print(f"Erro ao buscar vagas: {e}")
        return []

    finally:
        session.close()


# Busca uma vaga específica utilizando seu ID.
def buscar_vaga_por_id(vaga_id):
    session = SessionLocal()

    try:
        # Retorna a primeira vaga encontrada com o ID informado.
        vaga = session.query(Vaga).filter_by(vaga_id=vaga_id).first()
        return vaga

    except Exception as e:
        print(f"Erro ao buscar a vaga: {e}")
        return False

    finally:
        session.close()


# Atualiza o status de uma vaga já cadastrada.
def atualizar_status(vaga_id, novo_status):
    session = SessionLocal()

    try:
        # Localiza a vaga pelo ID.
        vaga = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        # Caso a vaga não exista, encerra a operação.
        if not vaga:
            return "Vaga não encontrada."

        # Atualiza o status da vaga.
        vaga.status = novo_status

        # Salva a alteração no banco de dados.
        session.commit()

        return "Status atualizado com sucesso!"

    except Exception as e:
        # Reverte a transação em caso de erro.
        session.rollback()

        print(f"Erro ao atualizar status: {e}")
        return False

    finally:
        session.close()


# Remove uma vaga do banco de dados utilizando seu ID.
def deletar_vaga(vaga_id):
    session = SessionLocal()

    try:
        # Busca a vaga que será removida.
        vaga = session.query(Vaga).filter_by(vaga_id=vaga_id).first()

        if not vaga:
            return "Vaga não encontrada."

        # Remove a vaga da sessão e confirma a exclusão.
        session.delete(vaga)
        session.commit()

        return "Vaga deletada com sucesso!"

    except Exception as e:
        # Desfaz a transação caso ocorra algum erro.
        session.rollback()

        print(f"Erro: não foi possível deletar a vaga: {e}")
        return False

    finally:
        # Fecha a conexão com o banco de dados.
        session.close()