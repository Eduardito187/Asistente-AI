from __future__ import annotations

import re


class BloqueConclusionRiesgo:
    """SRP: en consultas tecnicas (specs concretos, uso profesional o
    requisitos cuantitativos), inyecta una directiva para que la respuesta
    final SIEMPRE incluya:

      1. Conclusion: 'Por que conviene' resumido en 2-3 puntos.
      2. Riesgo: limitaciones reales del producto recomendado (FreeDOS,
         8GB en lugar de 16GB pedidos, sin OIS confirmado, etc).
      3. Trade-off: que se pierde si elige la opcion mas barata vs la mas
         cara.

    Patron del feedback (Tecno Camon): 'la respuesta es tecnicamente rica
    pero le falta recomendacion comercial'."""

    # Senales de consulta tecnica (specs concretos, uso pro, criterios duros).
    _RX_TECNICA = re.compile(
        r"\b(?:autocad|civil\s*3d|render|edici[oó]n|gaming|streaming|"
        r"programac[ií]on|ingenier[ií]a|dise[nñ]o|3d)\b"
        r"|\b(?:gpu|ram|ssd|hdmi|hz|inverter|anc|ois|mp|mah)\b"
        r"|\b\d+\s*(?:gb|hz|ram|ssd|kg|litros|mp|mah|w|watts)\b"
        r"|\b(?:i[3579]|ryzen|core)\b",
        re.IGNORECASE,
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje or not cls._RX_TECNICA.search(mensaje):
            return None
        return (
            "CONSULTA TECNICA — la respuesta DEBE cerrar con:\n"
            "  - **Por que conviene**: 2-3 puntos sintetizando specs vs uso del cliente.\n"
            "  - **Riesgo**: limitaciones reales del producto recomendado "
            "(ej: 'no confirma GPU dedicada en ficha', 'viene con FreeDOS', "
            "'tiene 8GB cuando pediste 16GB'). NO omitir riesgos por cortesia.\n"
            "  - **Trade-off**: si listas 2+ opciones, una frase explicando que "
            "se pierde con la mas barata vs lo que se gana con la mas cara."
        )
