from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class CpuTier(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"
    FLAGSHIP = "flagship"


class CpuSufijo(str, Enum):
    """Sufijo de movilidad del CPU. U/Y = bajo consumo (eficiencia).
    H/HS/HX = alto rendimiento (laptops gamer/workstation). K = desktop oc."""

    EFICIENCIA = "U"
    RENDIMIENTO = "H"
    DESKTOP = "K"
    DESCONOCIDO = "?"


@dataclass(frozen=True)
class CpuInfo:
    tier: CpuTier
    sufijo: CpuSufijo
    familia: str
    generacion: int | None = None


class DetectorCpuTier:
    """SRP: extraer tier (i3/i5/i7/i9 / Ryzen 3-9) y sufijo (U/H/HS) del CPU.

    Para uso profesional/render, un i7 con sufijo U (ultrabook) NO es
    equivalente a un i5 H (rendimiento). Esto permite al reranker
    distinguirlos al recomendar."""

    _RX_I3 = re.compile(r"\b(?:core\s*)?i3[\s-]*(\d{4,5})?([uhskpgyf]+)?\b", re.IGNORECASE)
    _RX_I5 = re.compile(r"\b(?:core\s*)?i5[\s-]*(\d{4,5})?([uhskpgyf]+)?\b", re.IGNORECASE)
    _RX_I7 = re.compile(r"\b(?:core\s*)?i7[\s-]*(\d{4,5})?([uhskpgyf]+)?\b", re.IGNORECASE)
    _RX_I9 = re.compile(r"\b(?:core\s*)?i9[\s-]*(\d{4,5})?([uhskpgyf]+)?\b", re.IGNORECASE)
    _RX_RYZEN = re.compile(r"\bryzen\s*(\d)[\s-]*(\d{4})?([uhskpgyf]+)?\b", re.IGNORECASE)
    _RX_ULTRA = re.compile(r"\bcore\s*ultra\s*(\d)\b", re.IGNORECASE)
    _RX_LOW = re.compile(r"\b(celeron|pentium|atom|n\d{4,5})\b", re.IGNORECASE)

    @classmethod
    def detectar(cls, texto: str) -> CpuInfo | None:
        if not texto:
            return None
        s = texto

        m = cls._RX_ULTRA.search(s)
        if m:
            num = int(m.group(1))
            tier = CpuTier.FLAGSHIP if num >= 9 else (CpuTier.HIGH if num >= 7 else CpuTier.MID)
            return CpuInfo(tier=tier, sufijo=CpuSufijo.RENDIMIENTO, familia=f"Core Ultra {num}")

        m = cls._RX_I9.search(s)
        if m:
            return CpuInfo(
                tier=CpuTier.FLAGSHIP,
                sufijo=cls._sufijo(m.group(2)),
                familia="i9",
                generacion=cls._generacion(m.group(1)),
            )
        m = cls._RX_I7.search(s)
        if m:
            return CpuInfo(
                tier=CpuTier.HIGH,
                sufijo=cls._sufijo(m.group(2)),
                familia="i7",
                generacion=cls._generacion(m.group(1)),
            )
        m = cls._RX_I5.search(s)
        if m:
            return CpuInfo(
                tier=CpuTier.MID,
                sufijo=cls._sufijo(m.group(2)),
                familia="i5",
                generacion=cls._generacion(m.group(1)),
            )
        m = cls._RX_I3.search(s)
        if m:
            return CpuInfo(
                tier=CpuTier.LOW,
                sufijo=cls._sufijo(m.group(2)),
                familia="i3",
                generacion=cls._generacion(m.group(1)),
            )
        m = cls._RX_RYZEN.search(s)
        if m:
            num = int(m.group(1))
            tier = (
                CpuTier.FLAGSHIP if num >= 9
                else CpuTier.HIGH if num >= 7
                else CpuTier.MID if num >= 5
                else CpuTier.LOW
            )
            return CpuInfo(
                tier=tier,
                sufijo=cls._sufijo(m.group(3)),
                familia=f"Ryzen {num}",
            )
        if cls._RX_LOW.search(s):
            return CpuInfo(tier=CpuTier.LOW, sufijo=CpuSufijo.EFICIENCIA, familia="low-end")
        return None

    @staticmethod
    def _sufijo(letras: str | None) -> CpuSufijo:
        if not letras:
            return CpuSufijo.DESCONOCIDO
        s = letras.upper()
        if "H" in s:
            return CpuSufijo.RENDIMIENTO
        if "K" in s:
            return CpuSufijo.DESKTOP
        if "U" in s or "Y" in s:
            return CpuSufijo.EFICIENCIA
        return CpuSufijo.DESCONOCIDO

    @staticmethod
    def _generacion(modelo: str | None) -> int | None:
        if not modelo or len(modelo) < 4:
            return None
        digits = modelo[:2] if modelo[0] != "0" else modelo[:1]
        try:
            return int(digits) if int(digits) <= 15 else int(modelo[0])
        except ValueError:
            return None

    @classmethod
    def es_alto_rendimiento(cls, info: CpuInfo | None) -> bool:
        if info is None:
            return False
        if info.tier in (CpuTier.HIGH, CpuTier.FLAGSHIP) and info.sufijo == CpuSufijo.RENDIMIENTO:
            return True
        if info.tier == CpuTier.FLAGSHIP:
            return True
        return False
