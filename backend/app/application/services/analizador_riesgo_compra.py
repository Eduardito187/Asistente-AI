from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelRiesgo(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


@dataclass(frozen=True)
class EvaluacionRiesgo:
    nivel: NivelRiesgo
    razones: list[str]
    badge: str  # icono / emoji corto para UI


class AnalizadorRiesgoCompra:
    """SRP: para cada producto recomendado, evaluar el riesgo de que el
    cliente quede insatisfecho. Riesgo = (datos faltantes) + (gama vs uso)
    + (precio vs valor) + (advertencias SO).

    El cliente nunca debe sentirse 'engatusado' — ver el riesgo le da
    transparencia."""

    @classmethod
    def evaluar(cls, producto, perfil) -> EvaluacionRiesgo:
        razones: list[str] = []
        score = 0  # mas score = mas riesgo

        from .advertencias_ficha_incompleta import AdvertenciasFichaIncompleta
        warns = AdvertenciasFichaIncompleta.advertencias(
            producto, getattr(perfil, "uso_declarado", None)
        )
        if warns:
            score += min(len(warns) * 15, 30)
            razones.append(f"{len(warns)} dato(s) faltante(s) en ficha")

        from .detector_gama_producto import DetectorGamaProducto, GamaProducto
        gama = DetectorGamaProducto.clasificar(producto)
        uso = (getattr(perfil, "uso_declarado", None) or "").lower()
        if uso in ("ingenieria", "diseno", "render", "programacion") and gama == GamaProducto.ENTRADA:
            score += 50
            razones.append(f"gama de entrada para uso {uso}")

        from .detector_sistema_operativo_producto import DetectorSistemaOperativoProducto
        adv_so = DetectorSistemaOperativoProducto.detectar(producto)
        if adv_so and adv_so.bloquea_uso_profesional and uso in (
            "ingenieria", "diseno", "render", "programacion"
        ):
            score += 60
            razones.append(adv_so.advertencia.split(" — ")[0])

        precio = float(producto.precio.monto)
        techo = getattr(perfil, "presupuesto_max", None)
        if techo and precio > techo * 1.10:
            score += 25
            razones.append("precio supera presupuesto")
        elif techo and precio > techo:
            score += 10
            razones.append("precio sobre el presupuesto declarado")

        gpu_req = getattr(perfil, "gpu_dedicada", None)
        if gpu_req and not getattr(producto, "gpu", None):
            score += 35
            razones.append("GPU dedicada no confirmada")

        if score >= 50:
            return EvaluacionRiesgo(NivelRiesgo.ALTO, razones, "🔴")
        if score >= 20:
            return EvaluacionRiesgo(NivelRiesgo.MEDIO, razones, "🟡")
        return EvaluacionRiesgo(NivelRiesgo.BAJO, razones or ["cumple lo critico"], "🟢")
