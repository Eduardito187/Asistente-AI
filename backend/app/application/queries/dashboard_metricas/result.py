from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResultadoDashboardMetricas:
    """DTO del dashboard de metricas (ventana deslizante en dias)."""

    dias: int
    turnos: int
    sesiones: int
    sesiones_con_orden: int
    pct_sesiones_cerraron: float
    pct_turnos_con_mentiras: float
    avg_ms: float
    p50_ms: int
    p95_ms: int
    por_ruta: list[dict] = field(default_factory=list)
    top_categorias: list = field(default_factory=list)
    top_ciudades: list = field(default_factory=list)
    pct_sin_resultado: float = 0.0
    pct_derivacion: float = 0.0
    alerta_sin_resultado: bool = False   # True si pct_sin_resultado > 30%
    alerta_derivacion: bool = False      # True si pct_derivacion > 15%
