import json
from pathlib import Path

from google import genai
from google.genai import types

from app.config.settings import GEMINI_API_KEY


class AnaliseService:

    def __init__(self):
        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        # analise_service.py
        #      ↓ parent
        # analise/
        #      ↓ parent.parent
        # IA/
        base_dir = Path(__file__).resolve().parent.parent

        caminho_curriculo = (
            base_dir
            / "curriculos"
            / "curriculo_base"
            / "curriculo_base.md"
        )

        self.curriculo = caminho_curriculo.read_text(
            encoding="utf-8"
        )

    def analisar(self, vaga):

        informacoes_vaga = {
            "titulo": vaga.titulo,
            "descricao": vaga.descricao,
            "localidade": vaga.localidade,
            "empresa": vaga.empresa
        }

        prompt = f"""
Você é um especialista em recrutamento de tecnologia,
análise de vagas e sistemas ATS.

Sua função é analisar uma vaga de emprego comparando-a
com o perfil profissional e currículo do candidato.

========================
REGRAS IMPORTANTES
========================

1. Nunca invente informações sobre o candidato.

2. Nunca considere que o candidato possui uma tecnologia,
experiência, curso, certificação, projeto ou conhecimento
que não esteja explicitamente presente no currículo ou
nas informações fornecidas.

3. Projetos pessoais NÃO devem ser tratados como experiência
profissional.

4. Não invente empresas, cargos, datas ou experiências.

5. Se uma informação não estiver disponível, informe que
ela não foi encontrada.

6. Não recomende adicionar ao currículo uma tecnologia
apenas porque ela aparece na vaga. Só recomende adicionar
algo se o candidato realmente possuir aquele conhecimento.

7. Avalie a compatibilidade de forma realista.

8. Localização é relevante para avaliar vagas presenciais
ou híbridas.

9. Educação pode ser considerada quando for requisito da vaga.

10. Não utilize características pessoais irrelevantes para
a capacidade profissional.

========================
PERFIL DO CANDIDATO
========================

Localização:
Osasco - SP, Brasil

Formação:
2º semestre de Análise e Desenvolvimento de Sistemas
no SENAI.

Área principal de interesse:
Backend.

Frontend:
Pode ser considerado quando fizer parte da vaga, mas não é
a principal área de interesse.

Conhecimentos informados:

- Java básico
- Python básico
- SQL básico
- APIs
- Spring Boot
- FastAPI
- Linux
- Redes
- HTML
- CSS
- Git
- GitHub
- Docker

O candidato possui projetos pessoais relevantes e um portfólio.

========================
CURRÍCULO BASE
========================

{self.curriculo}

========================
VAGA
========================

Título:
{informacoes_vaga["titulo"]}

Empresa:
{informacoes_vaga["empresa"]}

Localidade:
{informacoes_vaga["localidade"]}

Descrição:
{informacoes_vaga["descricao"]}

========================
ANÁLISE SOLICITADA
========================

Analise a vaga considerando:

- área principal
- área secundária
- nível da vaga
- modalidade
- adequação para estudante
- requisitos obrigatórios
- requisitos desejáveis
- tecnologias
- experiência exigida
- formação
- responsabilidades
- soft skills
- localização
- ATS
- compatibilidade entre candidato e vaga
- pontos fortes
- pontos fracos
- lacunas técnicas
- nível do candidato
- nível exigido pela vaga
- resumo profissional
- habilidades
- projetos relevantes
- experiência profissional
- estudos recomendados
- plano de ação
- recomendação de candidatura

A classificação da área deve utilizar preferencialmente:

BACKEND
FRONTEND
FULLSTACK
MOBILE
DATA
DEVOPS
CLOUD
QA
SEGURANÇA
REDES
SUPORTE
OUTRO

A recomendação de candidatura deve utilizar somente:

RECOMENDADA
RECOMENDADA_COM_RESSALVAS
POUCO_RECOMENDADA

A porcentagem de compatibilidade deve ser um número
entre 0 e 100.

A nota final também deve ser um número entre 0 e 100.

========================
FORMATO DA RESPOSTA
========================

Retorne SOMENTE JSON válido.

Não utilize Markdown.

Não coloque ```json.

Utilize exatamente esta estrutura:

{{
    "classificacao_vaga": {{
        "area_principal": "",
        "area_secundaria": "",
        "nivel": "",
        "modalidade": "",
        "adequada_para_estudante": true,
        "observacoes": ""
    }},

    "compatibilidade": {{
        "porcentagem": 0,
        "motivo": ""
    }},

    "candidatura": {{
        "recomendacao": "",
        "motivo": ""
    }},

    "pontos_fortes": [
        {{
            "titulo": "",
            "descricao": "",
            "relevancia": ""
        }}
    ],

    "pontos_fracos": [
        {{
            "titulo": "",
            "descricao": "",
            "impacto": "",
            "vale_estudar": true,
            "adicionar_somente_se_possuir": true
        }}
    ],

    "nivel": {{
        "nivel_vaga": "",
        "nivel_candidato": "",
        "comparacao": "",
        "observacao": ""
    }},

    "resumo_profissional": {{
        "atual": "",
        "melhorias": "",
        "sugestao": ""
    }},

    "habilidades": {{
        "manter": [],
        "priorizar": [],
        "reorganizar": [],
        "remover": [],
        "observacoes": ""
    }},

    "projetos": {{
        "mais_relevantes": [],
        "melhorias": []
    }},

    "experiencia": {{
        "melhorias": []
    }},

    "requisitos_obrigatorios": [
        {{
            "requisito": "",
            "status": "",
            "evidencia": ""
        }}
    ],

    "requisitos_desejaveis": [
        {{
            "requisito": "",
            "status": "",
            "evidencia": ""
        }}
    ],

    "ats": {{
        "presentes": [],
        "ausentes": []
    }},

    "estudos": [
        {{
            "titulo": "",
            "motivo": "",
            "prioridade": 1
        }}
    ],

    "plano_acao": [],

    "resumo_final": {{
        "maior_qualidade": "",
        "maior_lacuna": "",
        "maior_ponto_melhoria": "",
        "principal_estudo": "",
        "candidatura_recomendada": true,
        "nota_final": 0
    }}
}}
"""

        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        if not response.text:
            raise ValueError(
                "O Gemini não retornou nenhum conteúdo."
            )

        try:
            resultado = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"O Gemini retornou um JSON inválido: {e}"
            )

        return resultado