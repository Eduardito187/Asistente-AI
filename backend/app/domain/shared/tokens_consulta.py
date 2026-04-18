class TokensConsulta:
    """Servicio de dominio: extrae tokens significativos de una consulta conversacional."""

    STOPWORDS = frozenset({
        "disponible", "disponibles", "muestra", "muestrame", "muestren",
        "quiero", "comprar", "necesito", "busco", "buscar", "dame",
        "damelas", "damelos", "mostrar", "mostrarme", "mostrarte",
        "tengo", "opciones", "opcion", "alguna", "algun", "algunas", "algunos",
        "para", "con", "sin", "por", "una", "uno", "unos", "unas",
        "los", "las", "del", "que", "este", "esta", "estos", "estas",
        "mas", "muy", "solo", "todo", "todos", "todas", "toda",
        "son", "eso", "pero", "como", "cual", "cuales",
        "bueno", "buenos", "buena", "buenas", "barato", "barata",
        "baratos", "baratas", "caro", "cara", "caros", "caras",
        "hola", "tal", "favor", "porfa", "gracias",
    })
    MIN_LEN = 3

    @classmethod
    def significativos(cls, texto_normalizado: str) -> list[str]:
        if not texto_normalizado:
            return []
        return [
            t for t in texto_normalizado.split()
            if len(t) >= cls.MIN_LEN and t not in cls.STOPWORDS
        ]

    @classmethod
    def hay_terminos(cls, texto_normalizado: str) -> bool:
        return bool(cls.significativos(texto_normalizado))
