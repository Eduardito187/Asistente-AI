from __future__ import annotations

from ...domain.productos import Producto
from ..queries.obtener_perfil_sesion import ResultadoObtenerPerfilSesion
from .detector_cpu_tier import CpuSufijo, CpuTier, DetectorCpuTier


class CalculadorBoostUsoTecnico:
    """SRP: calcula boost de re-ranking basado en specs REALES del producto
    ponderadas segun el `uso_declarado` del cliente.

    P1.12 del review 2026-05-07. El reranker existente (`CalculadorBoostPerfil`)
    solo usaba match de palabras-clave del nombre — esto pondera por specs
    cuantitativas (ram_gb, capacidad_gb, gpu, cpu tier+sufijo, capacidad_kg,
    pulgadas) con pesos distintos por uso:

    - ingenieria/render/diseno: GPU(40) > RAM(20) > SSD(10) > CPU(10) > precio(5)
    - gaming                   : GPU(40) > CPU(20) > RAM(15) > refresh_hz(15) > precio(0)
    - oficina/estudio          : precio(20) > RAM(15) > SSD(10) > pantalla(5)
    - familia_grande           : capacidad_litros(40) > capacidad_kg(40) > precio(10)

    Si el cliente no declaro uso, devuelve 0 (no compite con el boost
    existente). Es aditivo a `CalculadorBoostPerfil.score()`."""

    # Pesos por uso. Cada uso es un dict de nombre_metrica -> peso.
    # Las metricas las traduce `_aporte_metrica()` a un valor [0,1] que
    # luego se multiplica por el peso.
    _PESOS: dict[str, dict[str, float]] = {
        "ingenieria":  {"gpu": 40, "ram": 20, "ssd": 10, "cpu_tier": 10, "cpu_h": 10, "presupuesto": 5},
        "render":      {"gpu": 40, "ram": 20, "ssd": 10, "cpu_tier": 10, "cpu_h": 10, "presupuesto": 5},
        "renderizado": {"gpu": 40, "ram": 20, "ssd": 10, "cpu_tier": 10, "cpu_h": 10, "presupuesto": 5},
        "diseno":      {"gpu": 30, "ram": 25, "ssd": 10, "cpu_tier": 10, "cpu_h": 5, "pantalla": 10, "presupuesto": 5},
        "edicion":     {"gpu": 30, "ram": 25, "ssd": 15, "cpu_tier": 10, "cpu_h": 5, "presupuesto": 5},
        "gaming":      {"gpu": 40, "cpu_tier": 20, "cpu_h": 10, "ram": 15, "refresh_hz": 15, "presupuesto": 0},
        "oficina":     {"presupuesto": 20, "ram": 15, "ssd": 10, "pantalla": 5},
        "estudio":     {"presupuesto": 20, "ram": 15, "ssd": 10, "pantalla": 5},
        "estudiante":  {"presupuesto": 20, "ram": 15, "ssd": 10, "pantalla": 5},
        "programacion":{"ram": 25, "ssd": 15, "cpu_tier": 10, "presupuesto": 10},
        "fotografia":  {"camara_mp": 30, "ram": 15, "ssd": 10, "pantalla": 10, "presupuesto": 5},
        "musica":      {"audio": 25, "presupuesto": 10},
        "viaje":       {"liviano": 30, "bateria": 20, "presupuesto": 10},
        "familia":     {"capacidad_litros": 40, "capacidad_kg": 40, "presupuesto": 10},
        "familia_grande": {"capacidad_litros": 40, "capacidad_kg": 40, "presupuesto": 10},
    }

    @classmethod
    def score(
        cls,
        producto: Producto,
        perfil: ResultadoObtenerPerfilSesion,
    ) -> float:
        uso = (getattr(perfil, "uso_declarado", None) or "").lower().strip()
        if not uso:
            return 0.0
        pesos = cls._pesos_para_uso(uso)
        if not pesos:
            return 0.0
        return sum(
            peso * cls._aporte_metrica(producto, metrica, perfil)
            for metrica, peso in pesos.items()
        )

    @classmethod
    def _pesos_para_uso(cls, uso: str) -> dict[str, float]:
        if uso in cls._PESOS:
            return cls._PESOS[uso]
        # Sinonimos / fragmentos: 'autocad' -> ingenieria, '3d' -> render, etc.
        for clave, mapping in (
            (("autocad", "civil 3d", "solidworks", "ingenieria", "ingenieria civil"), "ingenieria"),
            (("photoshop", "illustrator", "premiere", "after effects"), "edicion"),
            (("netflix", "youtube", "streaming"), "estudio"),
            (("juegos", "gamer"), "gaming"),
        ):
            if any(k in uso for k in clave):
                return cls._PESOS[mapping]
        return {}

    @classmethod
    def _aporte_metrica(
        cls,
        p: Producto,
        metrica: str,
        perfil: ResultadoObtenerPerfilSesion,
    ) -> float:
        """Devuelve un valor [0,1] indicando cuanto el producto cumple esa
        metrica. Las funciones helper se eligen por nombre de metrica."""
        return cls._DESPACHADOR.get(metrica, lambda *_: 0.0)(p, perfil)

    @staticmethod
    def _aporte_gpu(p: Producto, _: object) -> float:
        return 1.0 if getattr(p, "gpu", None) else 0.0

    @staticmethod
    def _aporte_ram(p: Producto, _: object) -> float:
        ram = getattr(p, "ram_gb", None) or 0
        if ram >= 32:
            return 1.0
        if ram >= 16:
            return 0.7
        if ram >= 8:
            return 0.3
        return 0.0

    @staticmethod
    def _aporte_ssd(p: Producto, _: object) -> float:
        ssd = getattr(p, "capacidad_gb", None) or 0
        if ssd >= 1024:
            return 1.0
        if ssd >= 512:
            return 0.7
        if ssd >= 256:
            return 0.3
        return 0.0

    @staticmethod
    def _aporte_cpu_tier(p: Producto, _: object) -> float:
        info = DetectorCpuTier.detectar(p.nombre or "")
        if info is None:
            return 0.0
        return {
            CpuTier.FLAGSHIP: 1.0,
            CpuTier.HIGH: 0.7,
            CpuTier.MID: 0.4,
            CpuTier.LOW: 0.0,
        }.get(info.tier, 0.0)

    @staticmethod
    def _aporte_cpu_h(p: Producto, _: object) -> float:
        """+1 si el CPU es sufijo H/HX (rendimiento). 0 si U (eficiencia)."""
        info = DetectorCpuTier.detectar(p.nombre or "")
        if info is None:
            return 0.0
        return 1.0 if info.sufijo == CpuSufijo.RENDIMIENTO else 0.0

    @staticmethod
    def _aporte_refresh_hz(p: Producto, _: object) -> float:
        hz = getattr(p, "refresh_hz", None) or 0
        if hz >= 144:
            return 1.0
        if hz >= 120:
            return 0.7
        if hz >= 90:
            return 0.3
        return 0.0

    @staticmethod
    def _aporte_pantalla(p: Producto, _: object) -> float:
        pulgadas = getattr(p, "pulgadas", None) or 0
        if pulgadas >= 15:
            return 1.0
        if pulgadas >= 13:
            return 0.6
        return 0.0

    @staticmethod
    def _aporte_camara_mp(p: Producto, _: object) -> float:
        mp = getattr(p, "camara_mp", None) or 0
        if mp >= 64:
            return 1.0
        if mp >= 48:
            return 0.7
        if mp >= 12:
            return 0.3
        return 0.0

    @staticmethod
    def _aporte_capacidad_litros(p: Producto, _: object) -> float:
        l = getattr(p, "capacidad_litros", None) or 0
        if l >= 400:
            return 1.0
        if l >= 300:
            return 0.7
        if l >= 200:
            return 0.3
        return 0.0

    @staticmethod
    def _aporte_capacidad_kg(p: Producto, _: object) -> float:
        kg = getattr(p, "capacidad_kg", None) or 0
        if kg >= 18:
            return 1.0
        if kg >= 13:
            return 0.5
        if kg >= 9:
            return 0.2
        return 0.0

    @staticmethod
    def _aporte_audio(p: Producto, _: object) -> float:
        # Heuristica simple: marca conocida de audio o presencia de keyword.
        nombre = (p.nombre or "").lower()
        return 1.0 if any(k in nombre for k in ("bose", "jbl", "sony", "harman", "anc")) else 0.0

    @staticmethod
    def _aporte_liviano(p: Producto, _: object) -> float:
        # Sin campo `peso_kg` confiable; aproximamos por pulgadas chicas.
        pulg = getattr(p, "pulgadas", None) or 0
        if 0 < pulg <= 13.3:
            return 1.0
        if pulg <= 14:
            return 0.5
        return 0.0

    @staticmethod
    def _aporte_bateria(p: Producto, _: object) -> float:
        mah = getattr(p, "bateria_mah", None) or 0
        if mah >= 5000:
            return 1.0
        if mah >= 4000:
            return 0.5
        return 0.0

    @staticmethod
    def _aporte_presupuesto(p: Producto, perfil) -> float:
        """1 si esta ampliamente bajo presupuesto, 0.5 si justo, 0 si fuera."""
        presupuesto = getattr(perfil, "presupuesto_max", None)
        if not presupuesto:
            return 0.5
        precio = float(p.precio.monto)
        if precio <= 0.7 * presupuesto:
            return 1.0
        if precio <= presupuesto:
            return 0.6
        return 0.0


# Despachador de metrica -> funcion. En Python no se puede declarar
# como atributo de clase referenciando a si misma, lo seteamos despues.
CalculadorBoostUsoTecnico._DESPACHADOR = {
    "gpu": CalculadorBoostUsoTecnico._aporte_gpu,
    "ram": CalculadorBoostUsoTecnico._aporte_ram,
    "ssd": CalculadorBoostUsoTecnico._aporte_ssd,
    "cpu_tier": CalculadorBoostUsoTecnico._aporte_cpu_tier,
    "cpu_h": CalculadorBoostUsoTecnico._aporte_cpu_h,
    "refresh_hz": CalculadorBoostUsoTecnico._aporte_refresh_hz,
    "pantalla": CalculadorBoostUsoTecnico._aporte_pantalla,
    "camara_mp": CalculadorBoostUsoTecnico._aporte_camara_mp,
    "capacidad_litros": CalculadorBoostUsoTecnico._aporte_capacidad_litros,
    "capacidad_kg": CalculadorBoostUsoTecnico._aporte_capacidad_kg,
    "audio": CalculadorBoostUsoTecnico._aporte_audio,
    "liviano": CalculadorBoostUsoTecnico._aporte_liviano,
    "bateria": CalculadorBoostUsoTecnico._aporte_bateria,
    "presupuesto": CalculadorBoostUsoTecnico._aporte_presupuesto,
}
