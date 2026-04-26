from __future__ import annotations

import re


class DetectorGpuDedicada:
    """SRP: detecta cuando el cliente exige GPU dedicada explícitamente.

    Señales directas de GPU: "gráfica dedicada", "GPU dedicada", marcas/modelos
    concretos (RTX, GTX, GeForce, NVIDIA, Radeon RX), o software 3D/CAD que
    requiere GPU dedicada obligatoriamente (AutoCAD, SolidWorks, renderizado).

    Cuando se activa, la búsqueda debe restringirse a productos cuyo campo
    `gpu` esté confirmado en la ficha. Si no hay resultados, el agente
    informa "No tengo ese dato en la ficha técnica" en lugar de recomendar
    laptops con GPU integrada."""

    _RX = re.compile(
        r"\b(?:"
        r"gr[aá]fica\s+dedicada|gpu\s+dedicada|tarjeta\s+(?:gr[aá]fica|dedicada)"
        r"|nvidia|geforce|rtx\b|gtx\b|radeon\s+rx"
        r"|autocad|solidworks|revit|catia|ansys|blender"
        r"|renderizado|render(?:ing)?"
        r"|dise[nñ]o\s+3d|modelado\s+3d|animaci[oó]n\s+3d"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def requiere_gpu(cls, mensaje: str | None) -> bool:
        """True si el mensaje contiene señales explícitas de GPU dedicada."""
        return bool(cls._RX.search(mensaje or ""))
