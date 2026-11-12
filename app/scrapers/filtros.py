import re
import unicodedata


def normalizar(texto: str) -> str:
    texto = str(texto or "").lower()
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )
    # Converte siglas com pontos como "t.i." ou "t.i" em "ti"
    sem_acentos = re.sub(r"\bt\.i\.?\b", "ti", sem_acentos)
    sem_acentos = re.sub(r"\bi\.t\.?\b", "it", sem_acentos)
    return sem_acentos


def contem_palavra(texto: str, palavra: str) -> bool:
    """Compara termos inteiros (por exemplo, Java não casa com JavaScript)."""
    texto_normalizado = normalizar(texto)
    palavra_normalizada = normalizar(palavra)
    return bool(
        re.search(rf"(?<!\w){re.escape(palavra_normalizada)}(?!\w)", texto_normalizado)
    )


def safe_text(locator) -> str:
    """Lê o texto de um locator Playwright, retornando fallback previsível."""
    try:
        if locator.count() > 0:
            texto = locator.first.text_content()
            if texto:
                return re.sub(r"\s+", " ", texto).strip()
    except Exception:
        pass
    return "N/A"


AREAS_TECNOLOGIA = (
    # Desenvolvimento & Software
    "desenvolvimento",
    "desenvolvedor",
    "desenvolvedora",
    "developer",
    "dev",
    "programador",
    "programadora",
    "programming",
    "software",
    "engenheiro de software",
    "software engineer",
    "backend",
    "back end",
    "back-end",
    "full stack",
    "fullstack",
    "full-stack",
    "frontend",
    "front end",
    "front-end",
    "web",
    "sistemas",
    "analista de sistemas",
    "analista de ti",
    "analista de desenvolvimento",
    "system analyst",
    "business systems analyst",
    "tecnologia",
    "tecnologia da informacao",
    "ti",
    "it",
    # IA, Automação & Dados
    "inteligencia artificial",
    "ia",
    "ai",
    "rpa",
    "automacao",
    "dados",
    "data engineer",
    "engenharia de dados",
    "data analyst",
    "analista de dados",
    "banco de dados",
    "database",
    "dba",
    # Cloud, Infra, Suporte & Técnico/Eletrônica
    "cloud",
    "devops",
    "sre",
    "infraestrutura",
    "redes",
    "suporte",
    "suporte tecnico",
    "suporte de ti",
    "service desk",
    "help desk",
    "field service",
    "tecnico eletronico",
    "eletronico",
    "eletronica",
    "hardware",
    "manutencao de computadores",
    # Qualidade & Testes
    "qa",
    "quality assurance",
    "analista de qualidade",
    "testes",
    "tester",
)

NIVEIS_INICIAIS = (
    "estagio",
    "estagiario",
    "estagiaria",
    "intern",
    "internship",
    "junior",
    "jr",
    "trainee",
    "aprendiz",
    "jovem aprendiz",
    "primeiro emprego",
    "sem experiencia",
    "entry level",
    "entry-level",
    "early career",
    "associado",
    "associate",
    "assistente",
    "auxiliar",
    "i",
)

PROGRAMAS_ENTRADA = (
    "programa de estagio",
    "programas de estagio",
    "programa estagio",
    "internship program",
    "programa trainee",
    "programa de trainee",
    "jovens talentos",
    "talentos",
)

TECNOLOGIAS_PERFIL = (
    "java",
    "spring",
    "spring boot",
    "springboot",
    "python",
    "fastapi",
    "api",
    "apis",
    "rest",
    "rest api",
    "restful",
    "microsservicos",
    "microservices",
    "sql",
    "postgres",
    "postgresql",
    "mysql",
    "sqlite",
    "sqlalchemy",
    "supabase",
    "docker",
    "git",
    "github",
    "github actions",
    "linux",
    "aws",
    "postman",
    "swagger",
    "openapi",
    "html",
    "html5",
    "css",
    "css3",
    "playwright",
    "web scraping",
)

NIVEIS_FORA_DO_ALVO = (
    "pleno",
    "pl",
    "mid",
    "mid level",
    "mid-level",
    "senior",
    "sr",
    "staff",
    "especialista",
    "specialist",
    "spec",
    "esp",
    "architect",
    "arquiteto",
    "arquiteta",
    "tech lead",
    "team lead",
    "lead",
    "lider",
    "principal",
    "gerente",
    "manager",
    "head",
    "director",
    "diretor",
    "coordenador",
    "supervisor",
    "ii",
    "iii",
    "iv",
)

STACKS_FORA_DO_ALVO = (
    "delphi",
    "c++",
    "php",
    "laravel",
    "ruby",
    "cobol",
    "abap",
    "salesforce",
    "servicenow",
)

CARGOS_EXCLUIDOS = (
    "vendas",
    "comercial",
    "vendedor",
    "telemarketing",
    "recepcionista",
    "motorista",
    "limpeza",
    "enfermagem",
    "contabil",
    "fiscal",
    "juridico",
    "advogado",
    "rh",
    "recursos humanos",
    "recrutador",
    "tech recruiter",
    "direito",
    "contabilidade",
    "psicologia",
    "marketing",
)


def titulo_relevante(titulo: str, exigir_nivel_no_titulo: bool = False) -> bool:
    titulo_normalizado = normalizar(titulo)

    if any(contem_palavra(titulo_normalizado, termo) for termo in CARGOS_EXCLUIDOS):
        return False

    if any(contem_palavra(titulo_normalizado, termo) for termo in NIVEIS_FORA_DO_ALVO):
        return False

    if any(contem_palavra(titulo_normalizado, termo) for termo in STACKS_FORA_DO_ALVO):
        return False

    eh_programa_entrada = any(
        contem_palavra(titulo_normalizado, termo) for termo in PROGRAMAS_ENTRADA
    )
    if eh_programa_entrada:
        return True

    tem_area = any(contem_palavra(titulo_normalizado, termo) for termo in AREAS_TECNOLOGIA)
    tem_nivel_inicial = any(
        contem_palavra(titulo_normalizado, termo) for termo in NIVEIS_INICIAIS
    )
    tem_tecnologia = any(
        contem_palavra(titulo_normalizado, termo) for termo in TECNOLOGIAS_PERFIL
    )

    if not (tem_area or (tem_nivel_inicial and tem_tecnologia)):
        return False

    if exigir_nivel_no_titulo and not tem_nivel_inicial:
        return False

    return True


def descricao_relevante(descricao: str) -> bool:
    texto = normalizar(descricao)

    # 1. Reprova apenas se a vaga exigir senioridade alta sem aceitar júnior/estágio junto
    aceita_entrada = bool(
        re.search(r"\b(?:estagio|estagiario|junior|jr|trainee|iniciante|entry)\b", texto)
    )
    if not aceita_entrada:
        senioridade_exigida = re.search(
            r"\b(?:nivel|vaga|posicao|cargo|perfil|level|role)\b[^.\n]{0,40}"
            r"\b(?:pleno|mid|mid-level|senior|sr|staff|especialista|tech lead|team lead|principal)\b",
            texto,
        )
        if senioridade_exigida:
            return False

    # 2. Reprova exigência explícita de liderança técnica
    if re.search(r"\b(?:liderar tecnicamente|lideranca tecnica)\b", texto):
        return False

    # 3. Reprova 3+ anos de experiência obrigatória (ignora se for "desejável"/"diferencial" ou tempo de empresa)
    for linha in texto.splitlines():
        if any(termo in linha for termo in ("desejavel", "diferencial", "diferenciais", "no mercado", "de mercado", "historia")):
            continue

        exige_experiencia_avancada = re.search(
            r"\b(?:experiencia|vivencia|experience)\b[^.]{0,60}"
            r"(?:[3-9]|\d{2,})\s*\+?\s*(?:anos|years)\b",
            linha,
        )
        exige_anos_inverso = re.search(
            r"\b(?:[3-9]|\d{2,})\s*\+?\s*(?:anos|years)\s+(?:de\s+|of\s+)?(?:experiencia|vivencia|experience)\b",
            linha,
        )
        if exige_experiencia_avancada or exige_anos_inverso:
            return False

    return True


def calcular_aderencia_stack(titulo: str, descricao: str = "") -> list[str]:
    texto_completo = f"{titulo} {descricao}"
    encontradas = [
        tech.upper() if len(tech) <= 4 else tech.title()
        for tech in TECNOLOGIAS_PERFIL
        if contem_palavra(texto_completo, tech)
    ]
    return list(dict.fromkeys(encontradas))