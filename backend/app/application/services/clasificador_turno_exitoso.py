from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClasificacionTurno:
    es_exitoso: bool
    score: int
    razones: list[str]


class ClasificadorTurnoExitoso:
    """SRP: decidir si un turno (cliente_msg + respuesta) merece ser auto-curado
    como ejemplo few-shot. Heuristica conservadora: que tenga productos
    citados, no haya caido al fallback, y la respuesta tenga sustancia."""

    MIN_LARGO_RESPUESTA = 80
    MIN_PRODUCTOS_CITADOS = 1

    _SENIALES_FALLO = (
        "se me complico",
        "no encontre productos exactos",
        "decime que tipo de producto",
        "necesito un poco mas de contexto",
    )

    @classmethod
    def evaluar(
        cls,
        mensaje_usuario: str,
        respuesta: str,
        productos_citados: list,
        ruta: str | None = None,
        tiempo_ms: int | None = None,
        mentiras_detectadas: int = 0,
    ) -> ClasificacionTurno:
        razones: list[str] = []
        score = 0

        if mentiras_detectadas > 0:
            return ClasificacionTurno(
                es_exitoso=False, score=0,
                razones=[f"mentiras detectadas: {mentiras_detectadas}"],
            )

        respuesta_low = (respuesta or "").lower()
        if any(s in respuesta_low for s in cls._SENIALES_FALLO):
            return ClasificacionTurno(
                es_exitoso=False, score=0,
                razones=["respuesta contiene seniales de fallback"],
            )

        if len(respuesta or "") < cls.MIN_LARGO_RESPUESTA:
            return ClasificacionTurno(
                es_exitoso=False, score=0,
                razones=["respuesta demasiado corta"],
            )

        if len(productos_citados) >= cls.MIN_PRODUCTOS_CITADOS:
            score += 50
            razones.append(f"{len(productos_citados)} productos citados")

        if ruta and ruta.startswith("atajo_"):
            return ClasificacionTurno(
                es_exitoso=False, score=score,
                razones=["ruta atajo — no necesita curacion"],
            )

        if tiempo_ms is not None and tiempo_ms < 8000:
            score += 20
            razones.append("latencia baja")

        if len(respuesta or "") > 200:
            score += 15
            razones.append("respuesta sustancial")

        if any(c in mensaje_usuario.lower() for c in ("?", "que", "cual", "cuanto")):
            score += 15
            razones.append("mensaje fue pregunta")

        return ClasificacionTurno(
            es_exitoso=score >= 50,
            score=min(100, score),
            razones=razones,
        )
