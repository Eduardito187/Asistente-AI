from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RatioCalidadPrecio:
    sku: str
    ratio: float    # specs_normalizadas / precio_normalizado, mas alto = mejor
    rank: int       # 1 = mejor relacion calidad/precio en la lista
    mensaje: str


class ScoringCalidadPrecio:
    """SRP: dado un set de productos, calcular ratio Specs/Precio relativo.

    Specs ponderan: RAM*4 + SSD*2 + GPU*30 + CPU_tier*10 + pulgadas*1.
    El producto con mejor ratio recibe rank 1 y un mensaje destacado tipo
    'mejor relacion calidad/precio'."""

    @classmethod
    def calcular(cls, productos: list) -> list[RatioCalidadPrecio]:
        if not productos:
            return []
        ratios: list[tuple] = []
        for p in productos:
            specs = cls._specs_score(p)
            precio = max(float(p.precio.monto), 1.0)
            ratio = specs / precio * 1000
            ratios.append((p, specs, precio, ratio))
        ratios.sort(key=lambda x: x[3], reverse=True)
        out: list[RatioCalidadPrecio] = []
        for rank, (p, specs, precio, ratio) in enumerate(ratios, start=1):
            mensaje = cls._mensaje(rank, len(productos))
            out.append(RatioCalidadPrecio(
                sku=str(p.sku),
                ratio=round(ratio, 2),
                rank=rank,
                mensaje=mensaje,
            ))
        return out

    @staticmethod
    def _specs_score(p) -> float:
        from .detector_cpu_tier import CpuTier, DetectorCpuTier
        info = DetectorCpuTier.detectar(getattr(p, "procesador", "") or "")
        cpu_w = {
            CpuTier.LOW: 1, CpuTier.MID: 3,
            CpuTier.HIGH: 5, CpuTier.FLAGSHIP: 7,
        }.get(info.tier if info else CpuTier.LOW, 1)
        ram = getattr(p, "ram_gb", None) or 0
        ssd = getattr(p, "capacidad_gb", None) or 0
        gpu_score = 30 if getattr(p, "gpu", None) else 0
        pulg = getattr(p, "pulgadas", None) or 0
        return ram * 4 + ssd * 2 + gpu_score + cpu_w * 10 + pulg

    @staticmethod
    def _mensaje(rank: int, total: int) -> str:
        if rank == 1:
            return "Mejor relacion calidad/precio"
        if rank == 2:
            return "Buena relacion calidad/precio"
        if rank == total:
            return "Mas caro por especificaciones similares"
        return ""
