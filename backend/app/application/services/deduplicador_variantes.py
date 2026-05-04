from __future__ import annotations

import re
from typing import Iterable


class DeduplicadorVariantes:
    """SRP: agrupar productos del mismo modelo cuando solo cambia RAM/SSD.

    Caso tipico: 'Asus Vivobook X515 (8+256gb)' y 'Asus Vivobook X515 (16+512gb)'
    son variantes del mismo modelo. Mostrarlas como dos entradas separadas
    confunde al cliente. El dedup elige la variante mas alta (RAM, storage)
    como representante y descarta las demas."""

    _RX_FAMILIA = re.compile(
        r"^(.*?)(?:\s*[\(\[][^)]*[\)\]]|\s+\d+(?:gb|tb)\b|\s+\d+\+\d+).*$",
        re.IGNORECASE,
    )

    @classmethod
    def deduplicar(cls, productos: Iterable) -> list:
        """Devuelve la lista sin variantes redundantes. La regla:
        si hay >=2 productos con la misma familia (mismo prefijo de nombre,
        misma marca, misma subcategoria), se conserva el de mayor RAM y luego
        de mayor storage; los otros se descartan."""
        items = list(productos)
        if len(items) <= 1:
            return items
        agrupados: dict[tuple, list] = {}
        for p in items:
            clave = cls._clave_familia(p)
            agrupados.setdefault(clave, []).append(p)
        out: list = []
        for clave, grupo in agrupados.items():
            if len(grupo) == 1 or clave == ("",):
                out.extend(grupo)
                continue
            mejor = max(
                grupo,
                key=lambda x: (
                    getattr(x, "ram_gb", 0) or 0,
                    getattr(x, "capacidad_gb", 0) or 0,
                    -float(x.precio.monto),
                ),
            )
            out.append(mejor)
        out.sort(key=lambda p: items.index(p))
        return out

    @classmethod
    def _clave_familia(cls, producto) -> tuple:
        nombre = (getattr(producto, "nombre", "") or "").lower()
        marca = (getattr(producto, "marca", "") or "").lower()
        subcat = (getattr(producto, "subcategoria", "") or "").lower()
        m = cls._RX_FAMILIA.match(nombre)
        familia = m.group(1).strip() if m else nombre
        return (familia, marca, subcat)
