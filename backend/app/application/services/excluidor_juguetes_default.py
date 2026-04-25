from __future__ import annotations

from ...domain.shared.normalizacion import NormalizadorTexto


class ExcluidorJuguetesDefault:
    """SRP: agrega 'juguete' al filtro tipo_producto_excluye cuando la consulta
    NO pide juguetes explicitamente.

    Razon: el catalogo mezcla heladeras reales con 'heladera de juguete' bajo
    la subcategoria Refrigeradores. Sin este filtro, buscar 'heladera' devuelve
    juguetes en los primeros resultados (precio bajo). Simetrico para otros
    productos con versiones de juguete (cocinita, lavadora, etc).

    Solo se desactiva si el mensaje/query contiene palabras que indican interes
    explicito en juguetes — ahi queremos que aparezcan."""

    _GATILLOS_JUGUETE: frozenset[str] = frozenset({
        "juguete", "juguetes", "juego", "juguetitos",
        "muneca", "muneco", "munecas", "munecos",
        "niño", "ninho", "nino", "ninhos", "ninhas",
        "bebe", "bebes",
        "infantil", "infantiles",
        "toy", "toys",
    })

    @classmethod
    def debe_excluir(
        cls,
        query: str | None,
        categoria: str | None,
        subcategoria: str | None,
        mensaje_usuario: str | None = None,
    ) -> bool:
        if cls._tiene_gatillo(query):
            return False
        if cls._tiene_gatillo(categoria):
            return False
        if cls._tiene_gatillo(subcategoria):
            return False
        if cls._tiene_gatillo(mensaje_usuario):
            return False
        return True

    @classmethod
    def _tiene_gatillo(cls, texto: str | None) -> bool:
        if not texto:
            return False
        norm = NormalizadorTexto.normalizar(texto)
        tokens = set(norm.split())
        return bool(tokens & cls._GATILLOS_JUGUETE)
