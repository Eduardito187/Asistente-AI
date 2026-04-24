from __future__ import annotations

import re


class LimpiadorListaProductos:
    """Post-procesador: elimina bloques de producto numerados del texto cuando
    los cards visuales ya los muestran.

    Elimina cualquier linea que sea un item de lista numerada con nombre en
    negrita (con o sin precio/SKU inline). Si la linea siguiente es una linea
    de precio/SKU huerfana (sin bullet), tambien la elimina — eran parte del
    mismo bloque del LLM."""

    # Item numerado que comienza con N. o N) seguido de texto en negrita.
    _RX_ITEM_NUM = re.compile(r"^\s*\d+[.)]\s+\*{1,2}")
    # Linea huerfana de precio/SKU (sin bullet propio).
    _RX_PRECIO   = re.compile(r"\bBs[\s.]?\d", re.IGNORECASE)
    _RX_SKU      = re.compile(r"\[[A-Z0-9][A-Z0-9\-./]{2,}\]")
    _RX_BULLET   = re.compile(r"^\s*[-*•]|^\s*\d+[.)]\s")

    @classmethod
    def limpiar(cls, respuesta: str) -> str:
        if not respuesta:
            return respuesta
        lineas = respuesta.split("\n")
        resultado: list[str] = []
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            if cls._RX_ITEM_NUM.match(linea):
                # Saltar esta linea (item con nombre bold).
                i += 1
                # Si la siguiente linea no tiene bullet y es precio/SKU huerfano,
                # tambien la saltamos — era la segunda parte del mismo bloque.
                while i < len(lineas):
                    sig = lineas[i]
                    if not sig.strip():
                        i += 1
                        continue
                    if not cls._RX_BULLET.match(sig) and (
                        cls._RX_PRECIO.search(sig) or cls._RX_SKU.search(sig)
                    ):
                        i += 1
                    break
            else:
                resultado.append(linea)
                i += 1
        return re.sub(r"\n{3,}", "\n\n", "\n".join(resultado)).strip()
