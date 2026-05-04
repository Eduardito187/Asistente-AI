from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PuntajeComercial:
    sku: str
    score: int
    cumple: list[str]
    falta: list[str]
    advertencias: list[str]


class ScoringComercial:
    """SRP: convertir 'cumple/no cumple' en un puntaje 0-100.

    Reglas (sumables, max 100):
    - GPU dedicada confirmada cuando se exigio:    35
    - RAM >= minimo:                                20
    - SSD >= minimo:                                15
    - CPU dentro de tier (i5/Ryzen5+):              15
    - Dentro del presupuesto ideal:                 10
    - Datos completos para el uso:                   5

    Penalizaciones (descuenta del score base 100):
    - GPU N/D cuando se pidio:                     -25
    - SO bloqueante (Chromebook para ingenieria):  -50
    - Gama de entrada para uso profesional:        -30"""

    @classmethod
    def calcular(
        cls,
        producto,
        perfil,
    ) -> PuntajeComercial:
        score = 0
        cumple: list[str] = []
        falta: list[str] = []
        advertencias: list[str] = []

        ram_min = getattr(perfil, "ram_gb_min", None)
        ssd_min = getattr(perfil, "ssd_gb_min", None)
        gpu_req = getattr(perfil, "gpu_dedicada", None)
        precio_max = getattr(perfil, "presupuesto_max", None)
        ideal = getattr(perfil, "presupuesto_ideal", None)
        uso = getattr(perfil, "uso_declarado", None)

        if gpu_req:
            if getattr(producto, "gpu", None):
                score += 35
                cumple.append("GPU dedicada confirmada")
            else:
                score -= 25
                falta.append("GPU dedicada")
        if ram_min:
            ram = getattr(producto, "ram_gb", None) or 0
            if ram >= ram_min:
                score += 20
                cumple.append(f"RAM {ram}GB")
            else:
                falta.append(f"RAM minima {ram_min}GB")
        if ssd_min:
            ssd = getattr(producto, "capacidad_gb", None) or 0
            if ssd >= ssd_min:
                score += 15
                cumple.append(f"SSD {ssd}GB")
            else:
                falta.append(f"SSD minimo {ssd_min}GB")
        if cls._cpu_apto(producto, uso):
            score += 15
            cumple.append("CPU adecuado")
        precio = float(producto.precio.monto)
        if ideal and precio <= ideal:
            score += 10
            cumple.append("dentro de presupuesto ideal")
        elif precio_max and precio <= precio_max:
            score += 5
            cumple.append("dentro de presupuesto maximo")
        if cls._datos_completos(producto, uso):
            score += 5
            cumple.append("ficha completa")

        from .detector_gama_producto import DetectorGamaProducto, GamaProducto
        gama = DetectorGamaProducto.clasificar(producto)
        if uso in ("ingenieria", "diseno", "render", "programacion") and gama == GamaProducto.ENTRADA:
            score -= 30
            advertencias.append("Gama de entrada — riesgo para uso profesional")

        from .detector_sistema_operativo_producto import DetectorSistemaOperativoProducto
        adv_so = DetectorSistemaOperativoProducto.detectar(producto)
        if adv_so and adv_so.bloquea_uso_profesional and uso in (
            "ingenieria", "diseno", "render", "programacion"
        ):
            score -= 50
            advertencias.append(adv_so.advertencia)
        elif adv_so:
            advertencias.append(adv_so.advertencia)

        score = max(0, min(100, score))
        return PuntajeComercial(
            sku=str(producto.sku),
            score=score,
            cumple=cumple,
            falta=falta,
            advertencias=advertencias,
        )

    @staticmethod
    def _cpu_apto(producto, uso: str | None) -> bool:
        if uso not in ("ingenieria", "diseno", "render", "programacion"):
            return True
        from .detector_cpu_tier import CpuTier, DetectorCpuTier
        info = DetectorCpuTier.detectar(getattr(producto, "procesador", "") or "")
        return info is not None and info.tier in (CpuTier.MID, CpuTier.HIGH, CpuTier.FLAGSHIP)

    @staticmethod
    def _datos_completos(producto, uso: str | None) -> bool:
        from .advertencias_ficha_incompleta import AdvertenciasFichaIncompleta
        return not AdvertenciasFichaIncompleta.advertencias(producto, uso)
