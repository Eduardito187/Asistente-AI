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

    # GPU dedicada exigida — sea explícita o por uso profesional implícito
    _RX_GPU = re.compile(
        r"\b(?:gpu|gpu\s+dedicada|rtx|gtx|nvidia|geforce|gráfica\s+dedicada|"
        r"autocad|civil\s*3d|render|renderizado|3d\s+modeling|diseño\s+3d)\b",
        re.IGNORECASE,
    )

    # TV para consola/gaming donde el dato de refresh y HDMI es crítico
    _RX_TV_GAMING = re.compile(
        r"\b(?:ps5|ps\s*5|xbox|gaming|120\s*hz|hdmi\s*2[\.,]1)\b.*"
        r"\b(?:televisor?|tv|tele)\b"
        r"|\b(?:televisor?|tv|tele)\b.*"
        r"\b(?:ps5|ps\s*5|xbox|gaming|120\s*hz|hdmi\s*2[\.,]1)\b",
        re.IGNORECASE | re.DOTALL,
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        partes: list[str] = []

        if cls._RX_TECNICA.search(mensaje):
            partes.append(
                "CONSULTA TÉCNICA — la respuesta DEBE cerrar con:\n"
                "  - **Por qué conviene**: 2-3 puntos sintetizando características vs uso del cliente.\n"
                "  - **Riesgo**: limitaciones reales del producto recomendado "
                "(ej: 'no confirma GPU dedicada en ficha', 'viene con FreeDOS', "
                "'tiene 8GB cuando pediste 16GB'). NO omitir riesgos por cortesía.\n"
                "  - **Trade-off**: si listás 2+ opciones, una frase explicando qué "
                "se pierde con la más barata vs lo que se gana con la más cara."
            )

        if cls._RX_GPU.search(mensaje):
            partes.append(
                "GPU DEDICADA EXIGIDA — regla de render obligatoria:\n"
                "  Para CADA laptop que muestres, indicá explícitamente:\n"
                "  - Si el campo `gpu` está en la ficha: mostrar el valor (ej: 'RTX 4060').\n"
                "  - Si el campo `gpu` NO está o está vacío: escribí EXACTAMENTE "
                "'GPU: No tengo ese dato en la ficha técnica.' y marcala como "
                "'No confirmada para diseño/render' en el bloque de Riesgo.\n"
                "  Nunca supongas GPU por el nombre del modelo ni por el procesador."
            )

        if cls._RX_TV_GAMING.search(mensaje):
            partes.append(
                "DATOS TÉCNICOS TV GAMING — para cada TV listada, mostrar:\n"
                "  - Tasa de refresco: valor confirmado en ficha o exactamente "
                "'No tengo ese dato en la ficha técnica.'\n"
                "  - HDMI 2.1: confirmado o 'No tengo ese dato en la ficha técnica.'\n"
                "  En el bloque **Riesgo** indicar si esos datos no están confirmados. "
                "Si no están confirmados, NO usar la palabra 'gamer', 'gaming' ni "
                "'ideal para PS5' para esa TV."
            )

        return "\n\n".join(partes) if partes else None
