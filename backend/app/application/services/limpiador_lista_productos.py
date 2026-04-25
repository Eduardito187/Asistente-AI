from __future__ import annotations

import re


class LimpiadorListaProductos:
    """Post-procesador: elimina items de lista numerada que referencian productos
    cuando los cards visuales ya los muestran abajo.

    Un item cuenta como 'producto' si es numerado y tiene negrita, precio o SKU
    inline. Tambien consume las lineas huerfanas de precio/SKU que siguen."""

    _RX_ITEM_NUM  = re.compile(r"^\s*\d+[.)]\s+")
    _RX_BOLD      = re.compile(r"\*{1,2}")
    _RX_PRECIO    = re.compile(r"\bBs[\s.]?\d", re.IGNORECASE)
    _RX_SKU       = re.compile(r"\[[A-Z0-9][A-Z0-9\-./]{2,}\]")
    _RX_NEXT_NUM  = re.compile(r"^\s*\d+[.)]\s")
    _RX_BULLET    = re.compile(r"^\s*[-*•]\s")

    @classmethod
    def _es_item_producto(cls, linea: str) -> bool:
        if not cls._RX_ITEM_NUM.match(linea):
            return False
        return (
            bool(cls._RX_BOLD.search(linea))
            or bool(cls._RX_PRECIO.search(linea))
            or bool(cls._RX_SKU.search(linea))
        )

    @classmethod
    def _es_huerfana(cls, linea: str) -> bool:
        return bool(cls._RX_PRECIO.search(linea)) or bool(cls._RX_SKU.search(linea))

    @classmethod
    def _saltar_huerfanas(cls, lineas: list[str], i: int) -> int:
        """Avanza i consumiendo lineas del bloque producto ya removido:
        lineas vacias, precio/SKU huerfanos y bullets de detalle (specs)."""
        while i < len(lineas):
            sig = lineas[i]
            if not sig.strip():
                i += 1
                continue
            if cls._RX_NEXT_NUM.match(sig):
                break
            if cls._es_huerfana(sig) or cls._RX_BULLET.match(sig):
                i += 1
            else:
                break
        return i

    @classmethod
    def limpiar(cls, respuesta: str) -> str:
        if not respuesta:
            return respuesta
        lineas = respuesta.split("\n")
        resultado: list[str] = []
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            if cls._es_item_producto(linea):
                i = cls._saltar_huerfanas(lineas, i + 1)
            else:
                resultado.append(linea)
                i += 1
        return re.sub(r"\n{3,}", "\n\n", "\n".join(resultado)).strip()
