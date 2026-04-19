from __future__ import annotations

from .resultado_aserto import ResultadoAserto


class VerificadorTurno:
    """SRP: aplicar las 4 clases de aserto disponibles sobre un turno."""

    @classmethod
    def verificar(cls, turno: dict, respuesta: dict) -> list[ResultadoAserto]:
        texto = (respuesta.get("respuesta") or "").lower()
        tools_llamadas = {p.get("tool") for p in respuesta.get("pasos") or []}
        asertos: list[ResultadoAserto] = []
        asertos.extend(cls._debe_contener(turno, texto))
        asertos.extend(cls._no_debe_contener(turno, texto))
        asertos.extend(cls._tools_requeridas(turno, tools_llamadas))
        asertos.extend(cls._tools_requeridas_cualquiera(turno, tools_llamadas))
        asertos.extend(cls._tools_prohibidas(turno, tools_llamadas))
        return asertos

    @staticmethod
    def _debe_contener(turno: dict, texto: str) -> list[ResultadoAserto]:
        return [
            ResultadoAserto(
                nombre=f"debe_contener:{token}",
                ok=token.lower() in texto,
                detalle="" if token.lower() in texto else f"no aparecio «{token}»",
            )
            for token in turno.get("debe_contener") or []
        ]

    @staticmethod
    def _no_debe_contener(turno: dict, texto: str) -> list[ResultadoAserto]:
        return [
            ResultadoAserto(
                nombre=f"no_debe_contener:{token}",
                ok=token.lower() not in texto,
                detalle="" if token.lower() not in texto else f"aparecio «{token}»",
            )
            for token in turno.get("no_debe_contener") or []
        ]

    @staticmethod
    def _tools_requeridas(turno: dict, llamadas: set) -> list[ResultadoAserto]:
        return [
            ResultadoAserto(
                nombre=f"tool_requerida:{tool}",
                ok=tool in llamadas,
                detalle="" if tool in llamadas else f"no se llamo {tool}",
            )
            for tool in turno.get("tools_requeridas") or []
        ]

    @staticmethod
    def _tools_requeridas_cualquiera(turno: dict, llamadas: set) -> list[ResultadoAserto]:
        opciones = turno.get("tools_requeridas_cualquiera") or []
        if not opciones:
            return []
        ok = any(t in llamadas for t in opciones)
        return [
            ResultadoAserto(
                nombre=f"tools_cualquiera:{','.join(opciones)}",
                ok=ok,
                detalle="" if ok else f"no se llamo ninguna de {opciones}",
            )
        ]

    @staticmethod
    def _tools_prohibidas(turno: dict, llamadas: set) -> list[ResultadoAserto]:
        return [
            ResultadoAserto(
                nombre=f"tool_prohibida:{tool}",
                ok=tool not in llamadas,
                detalle="" if tool not in llamadas else f"se llamo {tool} y estaba prohibida",
            )
            for tool in turno.get("tools_prohibidas") or []
        ]
