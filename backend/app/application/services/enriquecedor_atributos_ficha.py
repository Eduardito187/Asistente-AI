from __future__ import annotations

import re
from dataclasses import replace


class EnriquecedorAtributosFichaIncompleta:
    """SRP: cuando el atributo critico (gpu, ram, ssd) no aparece en el campo
    estructurado del producto, intenta encontrarlo en la descripcion o en
    caracteristicas. Equivalente a 'consultar la ficha completa' antes de
    rendirse.

    No inventa datos: solo confirma valores explicitos en el texto."""

    _RX_GPU = re.compile(
        r"\b(rtx\s*\d{4}\s*\w*|gtx\s*\d{3,4}\s*\w*|"
        r"radeon\s*(?:rx\s*)?\d{3,4}\s*\w*|"
        r"geforce\s*(?:rtx|gtx|mx)\s*\d{3,4}|"
        r"nvidia\s+(?:rtx|gtx|mx)\s*\d{3,4})\b",
        re.IGNORECASE,
    )
    _RX_RAM = re.compile(
        r"(\d{1,3})\s*gb\s+(?:de\s+)?(?:ram|memoria)\b",
        re.IGNORECASE,
    )
    _RX_SSD = re.compile(
        r"(\d{2,4})\s*gb\s+(?:ssd|nvme|m\.?2|almacenamiento)\b",
        re.IGNORECASE,
    )

    @classmethod
    def enriquecer(cls, producto):
        """Devuelve una copia del Producto con campos faltantes completados
        desde descripcion/caracteristicas, si el texto los menciona."""
        texto = " ".join([
            getattr(producto, "descripcion", "") or "",
            getattr(producto, "descripcion_extendida", "") or "",
            getattr(producto, "caracteristicas", "") or "",
            getattr(producto, "nombre", "") or "",
        ])
        cambios: dict = {}
        if not getattr(producto, "gpu", None):
            m = cls._RX_GPU.search(texto)
            if m:
                cambios["gpu"] = m.group(1).strip().upper()
        if not getattr(producto, "ram_gb", None):
            m = cls._RX_RAM.search(texto)
            if m:
                try:
                    cambios["ram_gb"] = int(m.group(1))
                except ValueError:
                    pass
        if not getattr(producto, "capacidad_gb", None):
            m = cls._RX_SSD.search(texto)
            if m:
                try:
                    cambios["capacidad_gb"] = int(m.group(1))
                except ValueError:
                    pass
        if not cambios:
            return producto
        try:
            return replace(producto, **cambios)
        except TypeError:
            return producto
