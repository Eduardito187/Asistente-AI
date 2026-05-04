from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Proyeccion:
    anios: int
    razon: str
    aviso_envejecimiento: str | None


class ProyeccionLongevidad:
    """SRP: estimar cuantos anios sera vigente un producto para un uso dado.

    Reglas heuristicas (no clarividencia):
      - Laptop con 16GB+SSD+i5+ -> 4-5 anios para estudio/oficina
      - Laptop con 8GB+HDD+i3   -> 1-2 anios para uso intenso
      - TV OLED                  -> 6+ anios (panel envejece bien)
      - Smartphone flagship      -> 4 anios (updates SO)
      - Smartphone gama media    -> 2-3 anios

    Devuelve numero + justificacion + (opcional) aviso de upgrade temprano."""

    @classmethod
    def proyectar(cls, producto, uso: str | None) -> Proyeccion:
        cat = (getattr(producto, "categoria", "") or "").lower()
        subcat = (getattr(producto, "subcategoria", "") or "").lower()
        ram = getattr(producto, "ram_gb", None) or 0
        ssd = getattr(producto, "capacidad_gb", None) or 0
        cpu = getattr(producto, "procesador", "") or ""
        gpu = getattr(producto, "gpu", None)
        tipo_panel = (getattr(producto, "tipo_panel", "") or "").upper()

        if "laptop" in cat or "computador" in cat or "notebook" in subcat:
            return cls._laptop(ram, ssd, cpu, gpu, uso)
        if "tv" in cat or "televisor" in cat or "tv" in subcat:
            return cls._tv(tipo_panel)
        if "celular" in cat or "smartphone" in subcat or "telefono" in cat:
            return cls._smartphone(producto)
        return Proyeccion(anios=3, razon="estimacion generica", aviso_envejecimiento=None)

    @staticmethod
    def _laptop(ram: int, ssd: int, cpu: str, gpu: str | None, uso: str | None) -> Proyeccion:
        from .detector_cpu_tier import CpuTier, DetectorCpuTier
        info = DetectorCpuTier.detectar(cpu)
        cpu_tier = info.tier if info else CpuTier.LOW
        peso_uso = (uso or "").lower() in ("ingenieria", "render", "diseno", "gaming", "programacion")

        if cpu_tier == CpuTier.LOW or ram <= 4:
            return Proyeccion(
                anios=2,
                razon="entrada (Celeron/Pentium o 4GB RAM): para uso basico aguanta 2 anios.",
                aviso_envejecimiento="Para uso intenso se siente lenta a los 12-18 meses.",
            )
        if ram <= 8 and ssd <= 256:
            return Proyeccion(
                anios=3,
                razon="8GB/256GB cumple oficina/estudio por 3 anios; pesado a partir del ano 2.",
                aviso_envejecimiento="Para uso pesado conviene 16GB.",
            )
        if ram >= 16 and ssd >= 512 and cpu_tier in (CpuTier.MID, CpuTier.HIGH, CpuTier.FLAGSHIP):
            base = 5 if gpu else 4
            return Proyeccion(
                anios=base,
                razon="16GB+SSD512+CPU mid/high: vigente 4-5 anios incluso para uso intenso.",
                aviso_envejecimiento=None if gpu or not peso_uso else "Sin GPU dedicada queda corta para render/3D al ano 3.",
            )
        return Proyeccion(anios=3, razon="configuracion intermedia", aviso_envejecimiento=None)

    @staticmethod
    def _tv(panel: str) -> Proyeccion:
        if panel in ("OLED", "QNED", "QLED"):
            return Proyeccion(
                anios=7,
                razon=f"{panel} envejece muy bien — colores y angulos siguen vigentes 7+ anios.",
                aviso_envejecimiento=None,
            )
        if panel == "LED":
            return Proyeccion(
                anios=5,
                razon="LED estandar dura 5 anios sin degrade visible.",
                aviso_envejecimiento=None,
            )
        return Proyeccion(anios=4, razon="panel sin marcar — estimacion conservadora", aviso_envejecimiento=None)

    @staticmethod
    def _smartphone(producto) -> Proyeccion:
        precio = float(producto.precio.monto)
        if precio >= 6000:
            return Proyeccion(
                anios=4,
                razon="flagship: 4 anios de updates de SO y rendimiento estable.",
                aviso_envejecimiento=None,
            )
        if precio >= 2500:
            return Proyeccion(
                anios=3,
                razon="gama media: 3 anios util, despues bateria y SO se quedan atras.",
                aviso_envejecimiento="Considera reemplazo de bateria al ano 2-3.",
            )
        return Proyeccion(
            anios=2,
            razon="entrada: 2 anios para uso ligero.",
            aviso_envejecimiento="Apps pesadas y juegos pueden lagear pronto.",
        )
