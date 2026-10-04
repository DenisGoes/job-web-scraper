from app.database.connection import SessionLocal
from app.database.model import Vaga as VagaModel


class VagaRepository:

    def listar_todas_vagas(self):
        try:
            with SessionLocal() as session:
                return session.query(VagaModel).all()

        except Exception as e:
            print(f"Erro ao buscar vagas: {e}")
            return []

    def buscar_vaga_por_id(self, vaga_id):
        try:
            with SessionLocal() as session:
                return session.query(VagaModel).filter_by(
                    vaga_id=vaga_id
                ).first()

        except Exception as e:
            print(f"Erro ao buscar a vaga: {e}")
            return None

    def salvar(self, vaga):
        try:
            with SessionLocal() as session:

                vaga_existente = session.query(VagaModel).filter_by(
                    vaga_id=vaga.vaga_id
                ).first()

                if vaga_existente:
                    print("Vaga já existe no banco de dados.")
                    return False

                nova_vaga = VagaModel(
                    vaga_id=vaga.vaga_id,
                    fonte=vaga.fonte,
                    titulo=vaga.titulo,
                    empresa=vaga.empresa,
                    localidade=vaga.localidade,
                    salario=vaga.salario,
                    modelo_trabalho=vaga.modelo_trabalho,
                    descricao=vaga.descricao,
                    data_publicacao=vaga.data_publicacao,
                    link_vaga=vaga.link_vaga,
                    mensagem=vaga.mensagem,
                )

                session.add(nova_vaga)
                session.commit()

                print("Vaga salva com sucesso!")
                return True

        except Exception as e:
            print(f"Erro ao salvar vaga: {e}")
            return False

    def atualizar_vaga(self, vaga_id, novo_status):
        try:
            with SessionLocal() as session:

                vaga = session.query(VagaModel).filter_by(
                    vaga_id=vaga_id
                ).first()

                if not vaga:
                    return "Vaga não encontrada."

                vaga.status = novo_status

                session.commit()

                return "Status atualizado com sucesso!"

        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False

    def deletar_vaga(self, vaga_id):
        try:
            with SessionLocal() as session:

                vaga = session.query(VagaModel).filter_by(
                    vaga_id=vaga_id
                ).first()

                if not vaga:
                    return "Vaga não encontrada."

                session.delete(vaga)
                session.commit()

                return "Vaga deletada com sucesso!"

        except Exception as e:
            print(f"Erro ao deletar vaga: {e}")
            return False