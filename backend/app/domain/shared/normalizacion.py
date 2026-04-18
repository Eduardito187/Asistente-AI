import unicodedata


class NormalizadorTexto:
    """Servicio puro de dominio: quita tildes y pasa a minusculas."""

    @staticmethod
    def normalizar(texto: str | None) -> str:
        if not texto:
            return ""
        descompuesto = unicodedata.normalize("NFD", str(texto))
        sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
        return sin_tildes.lower().strip()
