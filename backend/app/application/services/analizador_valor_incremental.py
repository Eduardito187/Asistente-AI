from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalisisIncremental:
    """Resultado: 'vale la pena' subir presupuesto del barato al caro?"""
    delta_precio: float
    delta_ram: int
    delta_storage: int
    cambio_cpu_tier: bool
    cambio_gpu: bool
    vale_la_pena: bool
    razon: str


class AnalizadorValorIncremental:
    """SRP: comparar dos productos cuando el cliente pregunta 'vale la pena
    pagar mas por el de Bs Y'. Devuelve si el delta de specs justifica el
    delta de precio. Sin esto, el agente lo decide a ojo del LLM."""

    UMBRAL_RAM_GB = 8
    UMBRAL_STORAGE_GB = 256
    UMBRAL_PRECIO_RELATIVO = 0.30

    @classmethod
    def comparar(cls, barato, caro) -> AnalisisIncremental:
        precio_b = float(barato.precio.monto)
        precio_c = float(caro.precio.monto)
        delta_precio = precio_c - precio_b
        delta_ram = (caro.ram_gb or 0) - (barato.ram_gb or 0)
        delta_storage = (caro.capacidad_gb or 0) - (barato.capacidad_gb or 0)
        cambio_cpu = cls._cpu_mejora(barato.procesador, caro.procesador)
        cambio_gpu = cls._gpu_mejora(getattr(barato, "gpu", None), getattr(caro, "gpu", None))

        upgrades = sum([
            delta_ram >= cls.UMBRAL_RAM_GB,
            delta_storage >= cls.UMBRAL_STORAGE_GB,
            cambio_cpu,
            cambio_gpu,
        ])
        precio_relativo = delta_precio / max(precio_b, 1.0)
        vale = upgrades >= 2 or (upgrades >= 1 and precio_relativo <= cls.UMBRAL_PRECIO_RELATIVO)

        razones = []
        if delta_ram >= cls.UMBRAL_RAM_GB:
            razones.append(f"+{delta_ram}GB RAM")
        if delta_storage >= cls.UMBRAL_STORAGE_GB:
            razones.append(f"+{delta_storage}GB almacenamiento")
        if cambio_cpu:
            razones.append("CPU superior")
        if cambio_gpu:
            razones.append("GPU dedicada")
        if not razones:
            razones.append("sin diferencia tecnica relevante")
        razon = ", ".join(razones)
        return AnalisisIncremental(
            delta_precio=delta_precio,
            delta_ram=delta_ram,
            delta_storage=delta_storage,
            cambio_cpu_tier=cambio_cpu,
            cambio_gpu=cambio_gpu,
            vale_la_pena=vale,
            razon=razon,
        )

    @staticmethod
    def _cpu_mejora(barato: str | None, caro: str | None) -> bool:
        from .detector_cpu_tier import CpuTier, DetectorCpuTier
        b = DetectorCpuTier.detectar(barato or "")
        c = DetectorCpuTier.detectar(caro or "")
        if c is None:
            return False
        if b is None:
            return c.tier in (CpuTier.HIGH, CpuTier.FLAGSHIP)
        orden = [CpuTier.LOW, CpuTier.MID, CpuTier.HIGH, CpuTier.FLAGSHIP]
        return orden.index(c.tier) > orden.index(b.tier)

    @staticmethod
    def _gpu_mejora(gpu_b: str | None, gpu_c: str | None) -> bool:
        return bool(gpu_c) and not bool(gpu_b)
