from __future__ import annotations

import re


class SanitizadorQueryBusqueda:
    """SRP: anular el argumento `query` de buscar_productos cuando contiene
    frases conversacionales o señales de uso (no nombres de productos).

    El LLM a veces copia la frase entera del cliente como `query`, lo que
    genera MATCH() sin sentido contra el catálogo. Aquí cortamos esa vía:
    si detectamos una frase conversacional, devolvemos None y dejamos que
    los filtros estructurados del PerfilSesion rijan la búsqueda."""

    _RX_SPECS_PURAS = re.compile(
        r"^[\s\w]*\b(?:"
        r"\d+\s*hz\b"
        r"|hdmi\s*[\d.]*"
        r"|para\s+(?:ps[345]?|xbox|gaming|peliculas|futbol|netflix)"
        r")\b",
        re.IGNORECASE,
    )

    # Frases de uso/contexto que no son nombres de productos
    _RX_USO_DECLARADO = re.compile(
        r"(?:"
        r"\bvoy\s+a\s+usar\b"
        r"|\blo\s+(?:voy\s+a\s+)?usar\s+para\b"
        r"|\bes\s+para\b"
        r"|\bla\s+(?:voy\s+a\s+)?usar\s+para\b"
        r"|\bestudio\s+\w"
        r"|\bpara\s+(?:la\s+)?universidad\b"
        r"|\bpara\s+(?:el\s+)?trabajo\b"
        r"|\bpara\s+ingeniería\b"
        r"|\bnecesito\s+para\b"
        r"|\bla\s+necesito\s+para\b"
        r"|\bpara\s+(?:dise[ñn]o|programaci[oó]n|arquitectura|ingenier[ií]a)\b"
        r"|\bvarias?\s+pesta[ñn]as?\b"
        r"|\bde\s+vez\s+en\s+cuando\b"
        r"|\btrabajo\s+(?:pesado|intenso|profesional)\b"
        r")",
        re.IGNORECASE,
    )

    # Software profesional como query directo (sin nombre de producto)
    _RX_SOFTWARE_PURO = re.compile(
        r"^(?:[\s,]*(?:"
        r"autocad|civil[\s_]?3d|solidworks|revit|archicad|catia|ansys|"
        r"blender|cinema[\s_]?4d|3ds[\s_]?max|maya|unreal|unity|lumion|"
        r"photoshop|illustrator|premiere|davinci|after[\s_]?effects|indesign|"
        r"sketchup|rhino|rhinoceros|enscape|twinmotion|"
        r"docker|kubernetes|virtualbox|vmware|excel[\s_]?pesado|"
        r"render(?:izado)?|autocad"
        r")[\s,]*)+$",
        re.IGNORECASE,
    )

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
        r"|\bcual(?:es)?\s+(?:son|es|tiene|tienen|de\s+(?:esas|esos|estas|estos|ellas|ellos))\b"
        r"|\bhay\s+(?:alguno|alguna|algun|algunas|algunos)\b"
        r"|\btien(?:es|e|en)\s+(?:alguno|alguna|algun|algunas|algunos)\b"
        r"|\bsolo\s+(?:las|los|el|la|una|uno)\b"
        r"|\bde\s+(?:esas|esos|estas|estos|ellas|ellos)\s+cual(?:es)?\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def sanitizar(cls, texto: str | None) -> str | None:
        if not texto:
            return None
        if cls._RX_FRASE_CONVERSACIONAL.search(texto):
            return None
        if cls._RX_SPECS_PURAS.search(texto):
            return None
        if cls._RX_USO_DECLARADO.search(texto):
            return None
        if cls._RX_SOFTWARE_PURO.search(texto):
            return None
        return texto
