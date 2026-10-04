class Vaga:
    def __init__(self, vaga_id, fonte, titulo, link_vaga, empresa=None
                 , localidade=None, salario=None, modelo_trabalho=None, descricao=None, data_publicacao=None):
        self.vaga_id = vaga_id
        self.fonte = fonte
        self.titulo = titulo
        self.empresa = empresa
        self.localidade = localidade
        self.salario = salario
        self.modelo_trabalho = modelo_trabalho
        self.descricao = descricao
        self.data_publicacao = data_publicacao
        self.link_vaga = link_vaga

    