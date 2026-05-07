from __future__ import annotations

import re

from .category_consistency_validator import ResultadoValidacion
from ....domain.aprendizaje import ReasonCode


class NoBackendLeakValidator:
    """SRP: detecta exposicion de errores tecnicos en la respuesta
    (HTTP 5xx, traces Python, SQL errors, nginx HTML). Falla con
    BACKEND_ERROR_VISIBLE — debe nunca ocurrir en ejemplos curados."""

    _PATRONES = [
        re.compile(r"\bhttp\s*5\d\d\b", re.IGNORECASE),
        re.compile(r"\btraceback\b", re.IGNORECASE),
        re.compile(r"\b(sqlalchemy|psycopg|pymysql|mariadb)\.", re.IGNORECASE),
        re.compile(r"<html[^>]*>", re.IGNORECASE),
        re.compile(r"\bnginx\b", re.IGNORECASE),
        re.compile(r"<title>5\d\d", re.IGNORECASE),
        re.compile(r"\bbad\s*gateway\b", re.IGNORECASE),
        re.compile(r"\binternal\s*server\s*error\b", re.IGNORECASE),
    ]

    @classmethod
    def validar(cls, respuesta: str) -> ResultadoValidacion:
        if not respuesta:
            return ResultadoValidacion(True, ReasonCode.OK, "vacio")
        for patron in cls._PATRONES:
            if patron.search(respuesta):
                return ResultadoValidacion(
                    False, ReasonCode.BACKEND_ERROR_VISIBLE,
                    f"leak detectado: {patron.pattern}",
                )
        return ResultadoValidacion(True, ReasonCode.OK, "sin leaks")
