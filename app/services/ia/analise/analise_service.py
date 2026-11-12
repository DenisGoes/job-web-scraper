import json
from pathlib import Path
import time

from google import genai
from google.genai import types

from app.config.settings import GEMINI_API_KEY

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_CURRICULO_BASE = DIR_BASE / "curriculos" / "curriculo_base"

MODELOS_GEMINI = (
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
)

SYSTEM_PROMPT_ANALISE = """Você é um especialista em recrutamento técnico (ATS) e carreira em tecnologia.
Analise a compatibilidade entre o currículo-base do candidato e a vaga informada.
Extraia com máxima precisão TODAS as palavras-chave, tecnologias, metodologias, termos de domínio e sinônimos usados na descrição da vaga para otimização ATS legítima.

Retorne EXCLUSIVAMENTE um objeto JSON válido (sem markdown ou texto fora do JSON) seguindo exatamente esta estrutura:
{
  "classificacao_vaga": {
    "area_principal": "string",
    "area_secundaria": "string",
    "nivel": "string",
    "modalidade": "string",
    "adequada_para_estudante": true,
    "observacoes": "string"
  },
  "compatibilidade": {
    "porcentagem": 0,
    "motivo": "string"
  },
  "candidatura": {
    "recomendacao": "Sim | Não | Talvez",
    "motivo": "string"
  },
  "nivel": {
    "nivel_vaga": "string",
    "nivel_candidato": "string",
    "comparacao": "string",
    "observacao": "string"
  },
  "pontos_fortes": [
    {"titulo": "string", "descricao": "string", "relevancia": "Alta | Média | Baixa"}
  ],
  "pontos_fracos": [
    {"titulo": "string", "descricao": "string", "impacto": "Alto | Médio | Baixo", "vale_estudar": true}
  ],
  "requisitos_obrigatorios": [
    {"requisito": "string", "status": "Atende | Parcial | Não atende", "evidencia": "string"}
  ],
  "requisitos_desejaveis": [
    {"requisito": "string", "status": "Atende | Parcial | Não atende", "evidencia": "string"}
  ],
  "resumo_profissional": {
    "atual": "string",
    "melhorias": "string",
    "sugestao": "string"
  },
  "habilidades": {
    "manter": ["string"],
    "priorizar": ["string"],
    "reorganizar": ["string"],
    "remover": ["string"],
    "observacoes": "string"
  },
  "projetos": {
    "mais_relevantes": ["string"],
    "melhorias": ["string"]
  },
  "ats": {
    "presentes": ["string"],
    "ausentes": ["string"],
    "termos_exatos_vaga": ["string"],
    "sinonimos_e_variacoes": ["string"],
    "metodologias_e_soft_skills": ["string"]
  },
  "estudos": [
    {"prioridade": 1, "titulo": "string", "motivo": "string"}
  ],
  "plano_acao": ["string"],
  "resumo_final": {
    "maior_qualidade": "string",
    "maior_lacuna": "string",
    "maior_ponto_melhoria": "string",
    "principal_estudo": "string",
    "nota_final": 0,
    "candidatura_recomendada": true
  }
}"""


def criar_cliente_gemini() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada no ambiente.")
    return genai.Client(api_key=GEMINI_API_KEY)


def carregar_curriculo_base() -> str:
    caminho = DIR_CURRICULO_BASE / "curriculo_base.md"
    if not caminho.exists():
        raise FileNotFoundError(f"Currículo-base não encontrado em: {caminho}")
    return caminho.read_text(encoding="utf-8")


def gerar_com_fallback(
    client: genai.Client,
    contents: list,
    config: types.GenerateContentConfig,
) -> str:
    ultimo_erro = None
    for modelo in MODELOS_GEMINI:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=contents,
                config=config,
            )
            if response.text and response.text.strip():
                print(f"[Gemini] Resposta gerada com: {modelo}", flush=True)
                return response.text.strip()
            raise ValueError("Resposta vazia retornada pelo modelo.")
        except Exception as e:
            ultimo_erro = e
            print(f"[Gemini] Falha em {modelo}: {e}", flush=True)
            time.sleep(1.0)

    raise RuntimeError(f"Todos os modelos Gemini falharam. Último erro: {ultimo_erro}")


class AnaliseService:
    def __init__(self):
        self.client = criar_cliente_gemini()
        self.curriculo = carregar_curriculo_base()

    def analisar(self, vaga) -> dict:
        prompt = (
            f"CURRÍCULO-BASE DO CANDIDATO:\n{self.curriculo}\n\n"
            f"DADOS DA VAGA:\n"
            f"- Título: {vaga.titulo}\n"
            f"- Empresa: {vaga.empresa or 'Não informada'}\n"
            f"- Localidade: {vaga.localidade or 'Não informada'}\n"
            f"- Modelo de trabalho: {vaga.modelo_trabalho or 'Não informado'}\n"
            f"- Salário: {vaga.salario or 'Não informado'}\n"
            f"- Descrição completa:\n{vaga.descricao or 'Não informada'}"
        )

        texto_json = gerar_com_fallback(
            self.client,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_ANALISE,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        limpo = texto_json.strip()
        if limpo.startswith("```"):
            limpo = limpo.strip("`").removeprefix("json").strip()

        return json.loads(limpo)