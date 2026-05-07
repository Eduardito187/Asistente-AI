from __future__ import annotations

import re

from .category_consistency_validator import ResultadoValidacion
from ....domain.aprendizaje import ReasonCode


class ResponseFormatValidator:
    """SRP: chequea que cada producto citado este en el formato
    'Nombre — Bs precio [SKU]'. Si la respuesta cita SKUs sin el formato
    canonical o sin precio, falla con BAD_FORMAT."""

    _RX_SKU_BRACKET = re.compile(r"\[([A-Z0-9#\-_/]{4,})\]")
    _RX_LINEA_BIEN = re.compile(
        r".*?[—\-]\s*Bs\s*[\d.,]+\s*\[[A-Z0-9#\-_/]{4,}\]",
        re.IGNORECASE,
    )

    MIN_LARGO = 80
    MAX_PRODUCTOS = 5

    @classmethod
    def validar(cls, respuesta: str, productos: list[dict]) -> ResultadoValidacion:
        if not respuesta:
            return ResultadoValidacion(False, ReasonCode.BAD_FORMAT, "respuesta vacia")
        if len(respuesta) < cls.MIN_LARGO:
            return ResultadoValidacion(False, ReasonCode.BAD_FORMAT, f"largo<{cls.MIN_LARGO}")
        skus_citados = cls._RX_SKU_BRACKET.findall(respuesta)
        if len(skus_citados) > cls.MAX_PRODUCTOS:
            return ResultadoValidacion(
                False, ReasonCode.TOO_MANY_OPTIONS,
                f"{len(skus_citados)} productos citados",
            )
        return ResultadoValidacion(True, ReasonCode.OK, "formato ok")
