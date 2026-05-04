from __future__ import annotations

import re
from enum import Enum


class PerfilComprador(str, Enum):
    ESTUDIANTE = "estudiante"
    PROFESIONAL = "profesional"
    GAMER = "gamer"
    HOGAR = "hogar"
    REGALO = "regalo"
    EMPRESA = "empresa"
    GENERICO = "generico"


class DetectorPerfilComprador:
    """SRP: clasificar al cliente por perfil de uso. Permite que el system
    prompt y el reranker adapten tono y prioridades segun perfil."""

    _RX_ESTUDIANTE = re.compile(
        r"\b(estudio|universidad|colegio|cursando|estudiante|tarea|tesis)\b",
        re.IGNORECASE,
    )
    _RX_PROFESIONAL = re.compile(
        r"\b(trabajo|oficina|ingenieria|arquitectura|programacion|"
        r"profesional|chamba|chambeo|teletrabajo|freelance|consultor|render|"
        r"autocad|civil\s*3d|solidworks|revit|photoshop|illustrator|premiere)\b",
        re.IGNORECASE,
    )
    _RX_GAMER = re.compile(
        r"\b(gaming|gamer|jugar|juegos?|fortnite|cs\s*go|valorant|fifa|"
        r"call\s+of\s+duty|cod|streaming|stream|ps[45]|xbox|consola)\b",
        re.IGNORECASE,
    )
    _RX_HOGAR = re.compile(
        r"\b(casa|hogar|familia|cocina|sala|dormitorio|mama|papa|hijos|"
        r"hijo|hija|esposo|esposa|netflix|peliculas?|series)\b",
        re.IGNORECASE,
    )
    _RX_REGALO = re.compile(
        r"\b(regalo|regalar|aniversario|cumple\w*|navidad|dia\s+de(?:l|\s+la)\s+\w+|"
        r"sorpresa|para\s+(?:mi|un|una)\s+(?:novi|amig|herman|mam|pap|hij))\b",
        re.IGNORECASE,
    )
    _RX_EMPRESA = re.compile(
        r"\b(empresa|negocio|local|tienda|comercio|emprendimiento|startup|"
        r"facturacion|factura|nit|equipos?\s+para\s+(?:mi\s+)?(?:oficina|equipo))\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, mensaje: str) -> PerfilComprador:
        if not mensaje:
            return PerfilComprador.GENERICO
        t = mensaje
        if cls._RX_REGALO.search(t):
            return PerfilComprador.REGALO
        if cls._RX_EMPRESA.search(t):
            return PerfilComprador.EMPRESA
        if cls._RX_GAMER.search(t):
            return PerfilComprador.GAMER
        if cls._RX_PROFESIONAL.search(t):
            return PerfilComprador.PROFESIONAL
        if cls._RX_ESTUDIANTE.search(t):
            return PerfilComprador.ESTUDIANTE
        if cls._RX_HOGAR.search(t):
            return PerfilComprador.HOGAR
        return PerfilComprador.GENERICO

    _SALUDOS_POR_PERFIL: dict[PerfilComprador, str] = {
        PerfilComprador.ESTUDIANTE: "Para estudios, priorizo balance precio/desempeno y portabilidad.",
        PerfilComprador.PROFESIONAL: "Para uso profesional priorizo CPU potente, RAM y SSD rapido.",
        PerfilComprador.GAMER: "Para gaming priorizo GPU dedicada, refresh rate y SSD NVMe.",
        PerfilComprador.HOGAR: "Para hogar priorizo facilidad de uso, marca confiable y eficiencia energetica.",
        PerfilComprador.REGALO: "Como es regalo, voy a priorizar productos visualmente atractivos y con buena marca.",
        PerfilComprador.EMPRESA: "Para empresa priorizo durabilidad, soporte de marca y compatibilidad.",
        PerfilComprador.GENERICO: "",
    }

    @classmethod
    def hook_recomendacion(cls, perfil: PerfilComprador) -> str:
        return cls._SALUDOS_POR_PERFIL.get(perfil, "")
