from __future__ import annotations

import re


class SanitizadorQueryBusqueda:
    """SRP: anular el argumento `query` de buscar_productos cuando contiene
    frases conversacionales (pedido de asesoria, declaracion de presupuesto,
    manifestaciones de preferencia) en vez de un termino de producto.

    El LLM a veces copia la frase entera del cliente como `query`, lo que
    genera MATCH() sin sentido contra el catalogo (ej. '+30000*' a partir
    de "tengo presupuesto de 30000bs") y degrada al manejador de producto
    ausente con alternativas random. Aqui cortamos esa via: si detectamos
    una frase conversacional, devolvemos None y dejamos que los filtros
    estructurados del PerfilSesion (categoria, pulgadas, precio_max, marca)
    rijan la busqueda.

    Es puramente deterministico — regex sobre el texto crudo, sin LLM."""

    _RX_FRASE_CONVERSACIONAL = re.compile(
        r"(?:"
        r"\bcual(?:es)?\s+me\s+(?:conviene|convienen|recomienda|recomiendas|sugiere|sugieres|serviria|quedaria|iria)\b"
        r"|\bque\s+me\s+(?:recomienda|recomiendas|sugiere|sugieres|aconseja|aconsejas|conviene|convienen)\b"
        r"|\bcual\s+(?:es\s+)?(?:la\s+)?(?:mejor|mas\s+recomendable|mas\s+conveniente|mas\s+completa)\b"
        r"|\basesor(?:ame|arme|ar|eme|a|es)\b"
        r"|\baconseja(?:me|rme|r)?\b"
        r"|\bayuda(?:me|rme)?\s+a\s+(?:elegir|decidir|escoger)\b"
        r"|\b(?:tengo|mi|con|manejo)\s+(?:un\s+)?(?:pre[\s-]?supuesto|presu)\b"
        r"|\bpre[\s-]?supuesto\s+(?:de|es|maximo|max)\b"
        r"|\bhasta\s+(?:bs\.?\s*)?\d"
        r"|\bmaximo\s+(?:bs\.?\s*)?\d"
        r"|\bno\s+me\s+(?:interesa|importa|convence)\s+(?:la\s+)?marca\b"
        r"|\b(?:la\s+)?marca\s+(?:no\s+me\s+(?:importa|interesa)|me\s+da\s+igual|indiferente)\b"
        r"|\bme\s+da\s+(?:igual|lo\s+mismo)\b"
        r"|\bcualquier\s+marca\b"
        r"|\bquiero\s+que\s+me\s+(?:asesores|recomiendes|ayudes|ayude)\b"
        r"|\bque\s+opin(?:a|as|an)\b"
        r"|\bno\s+se\s+(?:cual|que|por\s+donde)\b"
        r"|\bestoy\s+(?:perdido|confundid[oa]|entre)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def sanitizar(cls, texto: str | None) -> str | None:
        if not texto:
            return None
        if cls._RX_FRASE_CONVERSACIONAL.search(texto):
            return None
        return texto
