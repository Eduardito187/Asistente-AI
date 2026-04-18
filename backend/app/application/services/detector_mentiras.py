from __future__ import annotations

from .reglas_mentira import REGLAS_MENTIRA


class DetectorMentiras:
    """Detecta si el texto del LLM afirma acciones que no ejecuto via tool calling."""

    def detectar(self, respuesta: str, tools_ejecutadas_ok: set[str]) -> list[str]:
        faltantes: list[str] = []
        for regla in REGLAS_MENTIRA:
            if regla.patron.search(respuesta) and regla.tool not in tools_ejecutadas_ok:
                faltantes.append(regla.tool)
        return faltantes
