import re
import unicodedata


# NORMALIZAÇÃO E UTILITÁRIOS
def normalizar(texto: str) -> str:
    texto = texto.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def contem_palavra(texto: str, palavra: str) -> bool:
    # \b evita casar "java" dentro de "javascript"
    return re.search(rf"\b{re.escape(palavra)}\b", texto) is not None


def safe_text(locator):
    if locator.count() > 0:
        texto = locator.text_content()
        if texto:
            return texto.strip()
    return "N/A"


# PALAVRAS-CHAVE
KEYWORDS = [
    "python",
    "fastapi",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "sqlite",
    "backend",
    "junior",
    "júnior",
    "estagio",
    "estágio",
    "trainee",
    "desenvolvedor",
    "engenheiro de software",
    "software engineer",
    "web",
    "web developer",
    "programa de estagio",
    "programa de estágio"
]

EXCLUDE_KEYWORDS = [
    "pleno",
    "senior",
    "sênior",
    "sr",
    "sr.",
    "especialista",
    "lead",
    "tech lead",
    "gerente",
    "coordenador",
    "supervisor",
    "ingles avancado",
    "inglês avançado",
    "fluente em ingles",
    "java",
    "kotlin",
    "android",
    "ios",
    "swift",
    "c#",
    ".net",
    "php",
    "ruby",
    "golang",
    "scada",
    "networking",
    "administrador de rede",
]

DESCRICAO_REPROVADOS = [
    "senior",
    "pleno",
    "especialista",
    "tech lead",
    "liderança",
    "experiência sólida",
    "solid experience",
    "5 anos",
    "6 anos",
    "7 anos",
    "8 anos",
    "5+ years",
    "6+ years",
    "7+ years",
    "advanced english",
    "inglês avançado"
]

# normaliza tudo depois que as funções já existem
KEYWORDS = [normalizar(k) for k in KEYWORDS]
EXCLUDE_KEYWORDS = [normalizar(k) for k in EXCLUDE_KEYWORDS]
DESCRICAO_REPROVADOS = [normalizar(p) for p in DESCRICAO_REPROVADOS]



# FILTROS
def titulo_relevante(titulo: str) -> bool:
    titulo_normalizado = normalizar(titulo)

    tem_keyword_positiva = any(
        contem_palavra(titulo_normalizado, k) for k in KEYWORDS
    )

    tem_keyword_excluida = any(
        contem_palavra(titulo_normalizado, k) for k in EXCLUDE_KEYWORDS
    )

    return tem_keyword_positiva and not tem_keyword_excluida


def descricao_relevante(descricao: str) -> bool:
    descricao = normalizar(descricao)

    return not any(
        contem_palavra(descricao, palavra)
        for palavra in DESCRICAO_REPROVADOS
    )