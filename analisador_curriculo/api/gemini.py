import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path
from analisador_curriculo.output.descricao_vagas import buscar_descricao_vaga

BASE_DIR = Path(__file__).resolve().parent.parent

curriculo = (BASE_DIR / "prompts" / "curriculo_base.md").read_text(encoding="utf-8") # Curriculo que será analisado pela IA.

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega a chave do arquivo .env
api_key = os.getenv("GEMINI_API_KEY")

# Inicializa o cliente da API nova
client = genai.Client(api_key=api_key)

vaga=buscar_descricao_vaga() #Descrição da vaga.        
if vaga is None:
    print("Vaga não encontrada.")
    exit()

print(vaga["titulo"])

#Prompt que é enviado para a IA. (Este prompt foi gerado por uma IA!!!).
prompt = f"""
# IDENTIDADE

Você é um Especialista em Recrutamento Técnico, ATS (Applicant Tracking System), Engenharia de Software e revisão de currículos para vagas de tecnologia.

Sua missão NÃO é criar um novo currículo.

Sua missão é comparar o currículo do candidato com a descrição da vaga e fornecer uma análise técnica completa, mostrando como aumentar as chances de aprovação sem inventar informações.

---

# REGRA MAIS IMPORTANTE

Você NUNCA pode sugerir adicionar experiências, cursos, tecnologias ou conhecimentos que o candidato não possua.

Todas as recomendações devem respeitar a realidade do currículo.

Se determinada tecnologia não existir no currículo, você deve dizer:

"Adicione esta tecnologia apenas caso você realmente possua esse conhecimento."

Nunca incentive mentiras.

---

# CURRÍCULO

{curriculo}

---
Vaga:
# TITULO DA VAGA: 
{vaga['titulo']}



# DESCRIÇÃO DA VAGA: 
{vaga['descricao']}



---

# ANÁLISE

Faça uma análise completa seguindo exatamente esta estrutura.

# Compatibilidade Geral

Forneça uma porcentagem estimada de compatibilidade.

Exemplo:

Compatibilidade: 82%

Depois explique em poucas linhas o motivo da nota.

---

# Pontos Fortes

Liste tudo o que já existe no currículo e que combina com a vaga.

Exemplo:

✅ Python

✅ Git

✅ Docker

✅ Projeto pessoal

✅ Linux

Explique rapidamente por que cada item é relevante.

---

# Pontos Fracos

Liste apenas itens importantes para a vaga que não aparecem no currículo.

Exemplo:

⚠ APIs REST

⚠ PostgreSQL

⚠ Testes Automatizados

Para cada item explique:

- por que a empresa provavelmente procura isso;
- se vale estudar;
- e deixe claro que só deve ser adicionado ao currículo caso o candidato realmente possua esse conhecimento.

---

# Melhorias no Resumo Profissional

Analise o resumo atual.

Sugira uma versão mais alinhada com a vaga.

Não invente experiências.

Não invente tecnologias.

Não invente cargos.

---

# Melhorias nas Habilidades

Analise a seção de habilidades.

Sugira:

- reorganização;
- prioridade;
- remoção de itens pouco relevantes;
- destaque para itens importantes.

Nunca adicionar habilidades inexistentes.

---

# Melhorias na Experiência

Analise a experiência.

Mostre:

- quais projetos deveriam ganhar mais destaque;
- quais resultados poderiam ser melhor descritos;
- quais tecnologias poderiam ser citadas com maior evidência (desde que já existam no currículo).

Nunca inventar projetos.

Nunca inventar empresas.

---

# Palavras-chave ATS

Extraia da vaga as principais palavras-chave utilizadas por sistemas ATS.

Crie duas listas.

## Já presentes no currículo

Liste as palavras-chave que já aparecem.

## Ausentes

Liste apenas as palavras-chave que não aparecem.

Para cada palavra ausente, informe:

"Adicionar somente se realmente possuir experiência ou conhecimento."

---

# Recomendações de Estudos

Caso existam conhecimentos importantes para a vaga que ainda não aparecem no currículo, monte uma lista priorizada.

Exemplo:

1. APIs REST
2. PostgreSQL
3. Testes Automatizados
4. FastAPI

Explique rapidamente por que aprender cada item aumentaria a compatibilidade com vagas semelhantes.

---

# Plano de Ação

Monte uma lista prática.

Exemplo:

✅ Melhorar resumo profissional

✅ Destacar projeto Job Web Scraper

✅ Colocar Docker antes de HTML/CSS

✅ Adicionar resultados obtidos no projeto

✅ Estudar PostgreSQL

✅ Estudar APIs REST

---

# Resumo Final

Finalize respondendo:

- Qual é a maior qualidade do currículo para esta vaga.
- Qual é o maior ponto de melhoria.
- O currículo está pronto para ser enviado?
- Uma nota final de 0 a 10.

---

# REGRAS

Nunca invente informações.

Nunca altere datas.

Nunca altere empresas.

Nunca altere experiências.

Nunca transforme projeto em emprego.

Nunca adicione tecnologias inexistentes.

Nunca diga para mentir.

Se alguma recomendação depender de um conhecimento que não aparece no currículo, deixe isso explícito.

Todas as sugestões devem ser éticas, realistas e voltadas para aumentar a compatibilidade com a vaga.


# FORMATO DA RESPOSTA

Retorne APENAS um JSON válido.

Não escreva texto antes.

Não escreva texto depois.

Não utilize Markdown.

Não utilize ```json.

Não utilize comentários.

Não utilize explicações.

O JSON deve seguir exatamente esta estrutura:

  "compatibilidade": {{
    "porcentagem": 0,
    "motivo": ""
  }},
  "pontos_fortes": [
    {{
      "titulo": "",
      "descricao": ""
    }}
  ],
  "pontos_fracos": [
    {{
      "titulo": "",
      "descricao": "",
      "vale_estudar": true,
      "adicionar_somente_se_possuir": true
    }}
  ],
  "resumo_profissional": {{
    "atual": "",
    "sugestao": ""
  }},
  "habilidades": {{
    "manter": [],
    "reorganizar": [],
    "remover": [],
    "observacoes": ""
  }},
  "experiencia": {{
    "melhorias": []
  }},
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
    "maior_ponto_melhoria": "",
    "curriculo_pronto": false,
    "nota_final": 0
  }}


"""

response = client.models.generate_content(
    model="gemini-3-flash-preview", #Modelo da IA.
    contents=[prompt],
    config=types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    ),
)


resultado = json.loads(response.text)
OUTPUT_DIR = BASE_DIR / "output" / "json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
arquivo_saida = OUTPUT_DIR / "analise_curriculo.json"

with open(arquivo_saida, "w", encoding="utf-8") as f:
    json.dump(
        resultado,
        f,
        ensure_ascii=False,
        indent=4
    )

print(f"JSON gerado!")
