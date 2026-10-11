import re
import unicodedata


def normalizar(texto: str) -> str:
    """Padroniza acentos e caixa para comparar textos em português/inglês."""
    texto = str(texto or "").lower()
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def contem_palavra(texto: str, palavra: str) -> bool:
    """Compara termos inteiros (por exemplo, Java não casa com JavaScript)."""
    texto_normalizado = normalizar(texto)
    palavra_normalizada = normalizar(palavra)
    return bool(
        re.search(rf"(?<!\w){re.escape(palavra_normalizada)}(?!\w)", texto_normalizado)
    )


def safe_text(locator):
    """Lê o texto de um locator Playwright, retornando fallback previsível."""
    try:
        if locator.count() > 0:
            texto = locator.first.text_content()
            if texto:
                return texto.strip()
    except Exception:
        pass
    return "N/A"


# Áreas e cargos compatíveis com o perfil do currículo-base: desenvolvimento,
# software, sistemas, web, backend/frontend e testes/qualidade de software.
AREAS_TECNOLOGIA = (
    "desenvolvimento",
    "desenvolvedor",
    "desenvolvedora",
    "developer",
    "programador",
    "programadora",
    "programming",
    "software",
    "engenheiro de software",
    "software engineer",
    "backend",
    "back end",
    "frontend",
    "front end",
    "full stack",
    "fullstack",
    "web",
    "sistemas",
    "analista de sistemas",
    "analista de ti",
    "tecnologia",
    "tecnologia da informacao",
    "qa",
    "quality assurance",
    "testes de software",
    "tester",
    "automacao de testes",
    "ti",
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
    "primeiro emprego",
    "sem experiencia",
    "entry level",
    "entry-level",
    "early career",
)

# Tecnologias confirmadas no currículo-base e informadas pelo usuário.
# Elas ajudam a identificar vagas técnicas quando o título é genérico.
TECNOLOGIAS_PERFIL = (
    "python",
    "java",
    "html",
    "html5",
    "css",
    "css3",
    "sql",
    "postgresql",
    "mysql",
    "sqlite",
    "fastapi",
    "api",
    "rest api",
    "docker",
    "git",
    "github",
    "linux",
    "playwright",
    "automacao",
    "web scraping",
    "telegram api",
    "github actions",
    "sqlalchemy",
    "supabase",
)

NIVEIS_FORA_DO_ALVO = (
    "pleno",
    "senior",
    "sr",
    "especialista",
    "tech lead",
    "team lead",
    "principal",
    "gerente",
    "coordenador",
    "supervisor",
)


def titulo_relevante(titulo: str) -> bool:
    """Mantém cargos de tecnologia alinhados a início de carreira."""
    titulo_normalizado = normalizar(titulo)
    tem_area = any(contem_palavra(titulo_normalizado, termo) for termo in AREAS_TECNOLOGIA)
    tem_nivel_inicial = any(
        contem_palavra(titulo_normalizado, termo) for termo in NIVEIS_INICIAIS
    )
    tem_tecnologia = any(
        contem_palavra(titulo_normalizado, termo) for termo in TECNOLOGIAS_PERFIL
    )
    tem_nivel_senior = any(
        contem_palavra(titulo_normalizado, termo) for termo in NIVEIS_FORA_DO_ALVO
    )

    # Ex.: "Estágio em Java" não cita desenvolvimento no título, mas combina
    # nível inicial com uma tecnologia do perfil.
    if not (tem_area or (tem_nivel_inicial and tem_tecnologia)) or tem_nivel_senior:
        return False

    # Cargos de tecnologia sem nível explícito continuam elegíveis para a
    # checagem da descrição, onde a experiência exigida pode ser avaliada.
    return True


def descricao_relevante(descricao: str) -> bool:
    """Remove requisitos claramente incompatíveis sem falsos positivos comuns."""
    texto = normalizar(descricao)

    # Só reprova senioridade quando ela está ligada ao nível/cargo da vaga;
    # menções a colegas seniores ou à estrutura da equipe não eliminam a vaga.
    senioridade_exigida = re.search(
        r"\b(?:nivel|vaga|posicao|cargo)\b[^.\n]{0,50}"
        r"\b(?:pleno|senior|sr|especialista|tech lead|team lead|principal)\b",
        texto,
    )
    if senioridade_exigida:
        return False

    # Três anos ou mais de experiência explícita costumam indicar uma vaga
    # distante de estágio/primeiro emprego; exigências de 1–2 anos permanecem.
    exige_experiencia_avancada = re.search(
        r"\b(?:experiencia|vivencia)\b[^.\n]{0,70}"
        r"\b(?:minima de|minimo de|de|acima de|mais de)?\s*"
        r"(?:3|[4-9]|\d{2,})\s*\+?\s*anos\b",
        texto,
    )
    if exige_experiencia_avancada:
        return False

    return True
