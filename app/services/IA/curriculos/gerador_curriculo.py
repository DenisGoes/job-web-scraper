from pathlib import Path

from docx import Document
from docx.shared import Pt
from google.genai import types

from app.services.IA.analise.analise_service import AnaliseService


class GeradorCurriculo:
    """Personaliza o currículo usando somente fatos presentes na base."""

    def __init__(self):
        self.analise_service = AnaliseService()
        self.imagem_modelo = (
            Path(__file__).resolve().parent
            / "curriculo_base"
            / "Modelo_curriculo.png"
        )

    def gerar_texto(self, vaga, analise):
        if not self.imagem_modelo.exists():
            raise FileNotFoundError(
                f"Imagem modelo do currículo não encontrada: {self.imagem_modelo}"
            )

        prompt = f"""Personalize o currículo-base para a vaga informada.

Use a imagem anexada somente como REFERÊNCIA VISUAL de layout e organização.
Siga sua hierarquia aproximada: nome e contatos no topo; resumo profissional;
habilidades; experiência e projetos; educação; atividades/formação complementar.
Use títulos claros, conteúdo conciso e bullets. Retorne em texto Markdown simples,
com títulos usando # e ## e listas usando -. Não gere comentários sobre o processo.

REGRAS DE FIDELIDADE:
- Use português brasileiro.
- Use somente fatos explicitamente presentes no currículo-base.
- A imagem é apenas um modelo visual: nunca copie nomes, contatos, cargos ou
  textos de exemplo que apareçam nela.
- Não invente experiências, tecnologias, resultados, datas, certificações ou métricas.
- Não apresente requisitos da vaga como competências do candidato.
- Omita informações ausentes; não preencha lacunas com conteúdo fictício.
- Use a análise para priorizar e reorganizar informações verdadeiras, sem alterar fatos.

CURRÍCULO-BASE:
{self.analise_service.curriculo}

ANÁLISE DA VAGA:
{analise}

DADOS DA VAGA:
Cargo: {vaga.titulo}
Empresa: {vaga.empresa or 'Não informada'}
Localidade: {vaga.localidade or 'Não informada'}
Descrição: {vaga.descricao or 'Não informada'}
"""

        image_bytes = self.imagem_modelo.read_bytes()
        response = self.analise_service.client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(temperature=0.2),
        )
        if not response.text or not response.text.strip():
            raise ValueError("A IA não retornou o currículo.")
        return response.text.strip()

    @staticmethod
    def criar_docx(texto, caminho):
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Pt(45)
        section.bottom_margin = Pt(45)
        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith("# "):
                doc.add_heading(linha[2:], level=1)
            elif linha.startswith("## "):
                doc.add_heading(linha[3:], level=2)
            elif linha.startswith(("- ", "• ")):
                doc.add_paragraph(linha[2:], style="List Bullet")
            else:
                doc.add_paragraph(linha)
        doc.save(Path(caminho))
