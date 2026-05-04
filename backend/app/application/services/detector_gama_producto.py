from __future__ import annotations

import re
from enum import Enum


class GamaProducto(str, Enum):
    """Clasificacion de gama orientada al ranking comercial.

    Define un orden de menor a mayor: ENTRADA < BASICO < INTERMEDIO < POTENTE
    < PREMIUM. GAMER y WORKSTATION son tags ortogonales (un producto puede
    ser POTENTE+GAMER, PREMIUM+WORKSTATION, etc.)."""

    ENTRADA = "entrada"
    BASICO = "basico"
    INTERMEDIO = "intermedio"
    POTENTE = "potente"
    PREMIUM = "premium"
    GAMER = "gamer"
    WORKSTATION = "workstation"


class DetectorGamaProducto:
    """SRP: clasificar la gama de un producto por sus specs.

    Permite que el reranker y el system_prompt distingan 'low-end' de
    'mid-range' sin ambiguedad. Para laptops/desktops la senal principal
    son CPU + RAM + storage type. Para celulares y TVs hay reglas propias
    pero menos profundas (precio + marca + pulgadas)."""

    _RX_LOWEND_CPU = re.compile(r"\b(celeron|pentium|atom|n\d{4})\b", re.IGNORECASE)
    _RX_I3 = re.compile(r"\b(i3|core\s*i3|ryzen\s*3)\b", re.IGNORECASE)
    _RX_I5 = re.compile(r"\b(i5|core\s*i5|ryzen\s*5)\b", re.IGNORECASE)
    _RX_I7 = re.compile(r"\b(i7|core\s*i7|ryzen\s*7|core\s*ultra\s*7)\b", re.IGNORECASE)
    _RX_I9 = re.compile(r"\b(i9|core\s*i9|ryzen\s*9|core\s*ultra\s*9|threadripper)\b", re.IGNORECASE)
    _RX_GPU_GAMING = re.compile(r"\b(rtx|gtx|radeon\s*rx|geforce)\b", re.IGNORECASE)
    _RX_GPU_PRO = re.compile(r"\b(quadro|rtx\s*a\d|tesla|firepro)\b", re.IGNORECASE)
    _RX_EMMC = re.compile(r"\bemmc\b", re.IGNORECASE)
    _RX_CHROME = re.compile(r"\b(chrome\s*os|chromebook)\b", re.IGNORECASE)

    @classmethod
    def clasificar(cls, producto) -> GamaProducto:
        nombre = (getattr(producto, "nombre", "") or "")
        cpu = (getattr(producto, "procesador", "") or "")
        gpu = (getattr(producto, "gpu", "") or "")
        ram = getattr(producto, "ram_gb", None)
        storage = getattr(producto, "capacidad_gb", None)
        texto = f"{nombre} {cpu}".strip()

        if cls._RX_GPU_PRO.search(gpu) or cls._RX_GPU_PRO.search(texto):
            return GamaProducto.WORKSTATION
        if cls._RX_GPU_GAMING.search(gpu) or cls._RX_GPU_GAMING.search(texto):
            return GamaProducto.GAMER
        if cls._RX_LOWEND_CPU.search(texto) or cls._RX_CHROME.search(nombre):
            return GamaProducto.ENTRADA
        if cls._RX_EMMC.search(nombre):
            return GamaProducto.ENTRADA
        if ram is not None and ram <= 4:
            return GamaProducto.ENTRADA
        if cls._RX_I9.search(texto):
            return GamaProducto.PREMIUM
        if cls._RX_I7.search(texto) and (ram or 0) >= 16:
            return GamaProducto.POTENTE
        if cls._RX_I5.search(texto) and (ram or 0) >= 16 and (storage or 0) >= 512:
            return GamaProducto.INTERMEDIO
        if cls._RX_I5.search(texto):
            return GamaProducto.INTERMEDIO
        if cls._RX_I3.search(texto):
            return GamaProducto.BASICO
        if (ram or 0) >= 16:
            return GamaProducto.INTERMEDIO
        if (ram or 0) >= 8:
            return GamaProducto.BASICO
        return GamaProducto.ENTRADA

    @classmethod
    def es_apto_para_uso_profesional(cls, producto) -> bool:
        gama = cls.clasificar(producto)
        return gama in {
            GamaProducto.INTERMEDIO,
            GamaProducto.POTENTE,
            GamaProducto.PREMIUM,
            GamaProducto.GAMER,
            GamaProducto.WORKSTATION,
        }
