from pathlib import Path
import re

from docx import Document
from docx.shared import Pt
from google.genai import types

from app.services.ia.analise.analise_service import (
    carregar_curriculo_base,
    criar_cliente_gemini,
    gerar_com_fallback,
)

SYSTEM_PROMPT_CURRICULO = """Você é um especialista sênior em otimização de currículos para sistemas ATS (Gupy, Greenhouse, Workday, Lever) e triagem técnica por IA.
Seu objetivo é maximizar o score de compatibilidade ATS do currículo para a vaga informada, mantendo 100% de honestidade factual.

ESTRUTURA OBRIGATÓRIA DO CURRÍCULO (Markdown limpo):
1. # Nome Completo
2. Linha de subtítulo alvo alinhada à vaga (ex.: **Desenvolvedor Backend | Java · Spring Boot · Python · APIs RESTful · Docker · PostgreSQL**)
3. Linha de contato: Cidade - Estado · Telefone · E-mail · LinkedIn · GitHub · Portfólio
4. ## Resumo Profissional
5. ## Habilidades Técnicas
6. ## Projetos & Experiência Prática
7. ## Formação Acadêmica
8. ## Formação Complementar

ESTRATÉGIA DE PALAVRAS-CHAVE ATS (ALTA DENSIDADE E NATURALIDADE):
- Espelhe os termos exatos da descrição da vaga e da análise ATS (ex.: se a vaga usa "APIs RESTful", "Microsserviços", "Containers", "CI/CD", "Banco de Dados Relacional", "Automação", "Integração de Sistemas", "Versionamento", incorpore essas expressões naturalmente onde o candidato já possui base real).
- Use variações e siglas + termos por extenso quando aplicável (ex.: "Git e GitHub (Controle de Versão)", "GitHub Actions (CI/CD)", "PostgreSQL (SQL / Banco de Dados Relacional)", "Docker (Containerização)").
- Distribua as palavras-chave prioritárias da vaga em três zonas críticas para o algoritmo ATS:
  a) Subtítulo e Resumo Profissional (6 a 10 palavras-chave centrais da vaga logo no topo);
  b) Seção de Habilidades Técnicas (agrupadas por categoria com termos exatos da vaga em destaque);
  c) Bullets dos Projetos (conectando ação + tecnologia + resultado técnico).
- PROIBIDO: Nunca gere texto oculto, listas desconexas de palavras-chave sem contexto (keyword stuffing) e nunca invente experiências, empresas, cargos, datas ou tecnologias que não existam no currículo-base.
- Idioma: português brasileiro. Retorne APENAS o Markdown final do currículo."""


class GeradorCurriculo:
    def __init__(self):
        self.client = criar_cliente_gemini()
        self.curriculo = carregar_curriculo_base()

    def gerar_texto(self, vaga, analise: dict) -> str:
        print(f"[Currículo] Iniciando geração ATS para vaga {vaga.id}...", flush=True)

        ats_info = analise.get("ats", {})
        habilidades_info = analise.get("habilidades", {})

        prompt = (
            f"CURRÍCULO-BASE DO CANDIDATO:\n{self.curriculo}\n\n"
            f"PALAVRAS-CHAVE PRIORITÁRIAS EXTRAÍDAS DA VAGA (ATS):\n"
            f"- Presentes no perfil: {ats_info.get('presentes', [])}\n"
            f"- Termos exatos da vaga: {ats_info.get('termos_exatos_vaga', [])}\n"
            f"- Sinônimos e variações: {ats_info.get('sinonimos_e_variacoes', [])}\n"
            f"- Metodologias e competências: {ats_info.get('metodologias_e_soft_skills', [])}\n"
            f"- Lacunas (NÃO inventar, apenas adaptar o que for correlato): {ats_info.get('ausentes', [])}\n"
            f"- Habilidades a priorizar: {habilidades_info.get('priorizar', [])}\n\n"
            f"DADOS DA VAGA ALVO:\n"
            f"- Cargo: {vaga.titulo}\n"
            f"- Empresa: {vaga.empresa or 'Não informada'}\n"
            f"- Localidade: {vaga.localidade or 'Não informada'}\n"
            f"- Descrição completa:\n{vaga.descricao or 'Não informada'}"
        )

        texto = gerar_com_fallback(
            self.client,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_CURRICULO,
                temperature=0.25,
            ),
        )
        print(f"[Currículo] Texto ATS gerado ({len(texto)} caracteres).", flush=True)
        return texto

    @staticmethod
    def _adicionar_texto_formatado(paragrafo, texto: str) -> None:
        partes = re.split(r"(\*\*.*?\*\*)", texto)
        for parte in partes:
            if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
                paragrafo.add_run(parte[2:-2]).bold = True
            elif parte:
                paragrafo.add_run(parte)

    @classmethod
    def criar_docx(cls, texto: str, caminho: str | Path) -> None:
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Pt(36)
        section.bottom_margin = Pt(36)
        section.left_margin = Pt(42)
        section.right_margin = Pt(42)

        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha or linha in ("---", "***"):
                continue

            if linha.startswith("# "):
                doc.add_heading(linha[2:].strip(), level=1)
            elif linha.startswith("## "):
                doc.add_heading(linha[3:].strip(), level=2)
            elif linha.startswith("### "):
                doc.add_heading(linha[4:].strip(), level=3)
            elif linha.startswith(("- ", "* ", "• ")):
                p = doc.add_paragraph(style="List Bullet")
                cls._adicionar_texto_formatado(p, linha[2:].strip())
            else:
                p = doc.add_paragraph()
                cls._adicionar_texto_formatado(p, linha)

        doc.save(Path(caminho))