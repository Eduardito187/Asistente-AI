from __future__ import annotations

import re


class BloqueTresSeccionesFiltros:
    """SRP: cuando el cliente declara requisitos cuantitativos duros
    (capacidad minima, tamanio minimo, requisito tecnico no negociable),
    inyecta directiva para que la respuesta agrupe los productos en
    tres secciones explicitas.

    Caso del feedback:
    - Lavadora min 18kg -> Hisense 19kg cumple, LG 13kg / Whirlpool 9kg
      no deberian aparecer mezcladas como recomendacion principal.
    - Refri familia 6 / no frigobar -> exhibidor y freezer NO van mezclados.

    El LLM ya tiene los productos en tool_call result; aqui solo le
    indicamos la estructura."""

    # Senales de requisito cuantitativo o exclusion categorica.
    _RX_REQUISITO_DURO = re.compile(
        r"\bm[ií]nimo\s+\d+\s*(?:kg|gb|litros?|pulgadas|hz|mah|mp)\b"
        r"|\bal\s+menos\s+\d+\s*(?:kg|gb|litros?|pulgadas|hz)\b"
        r"|\bm[áa]s\s+de\s+\d+\s*(?:kg|gb|litros?|pulgadas|hz)\b"
        r"|\bno\s+m[áa]s\s+chic[oa]s?\b|\bno\s+pequen[ñ]as?\b"
        r"|\bfamilia\s+(?:grande|de\s+\d+|numerosa)\b"
        r"|\b(?:no\s+(?:frigobar|exhibidor|freezer|mini)|"
        r"sin\s+(?:frigobar|exhibidor|freezer|mini))\b",
        re.IGNORECASE,
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje or not cls._RX_REQUISITO_DURO.search(mensaje):
            return None
        return (
            "FORMATO TRES SECCIONES (cliente declaro requisito duro):\n"
            "  **Cumple todo:** lista los productos que cumplen TODOS los "
            "requisitos cuantitativos (capacidad, RAM, GPU, etc).\n"
            "  **Cumple parcialmente:** productos que se acercan pero les "
            "falta UN requisito (ej. 'pediste 18kg, esta es de 16kg'). "
            "Marcar la diferencia explicitamente.\n"
            "  **No recomendado:** productos que incumplen mas de un requisito "
            "o quedan muy por debajo (ej. lavadora de 9kg si pediste 18kg).\n"
            "Si una seccion queda vacia, NO la imprimas. NO mezcles productos "
            "que no cumplen como si fueran 'opciones validas'."
        )
