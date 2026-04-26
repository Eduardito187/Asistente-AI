from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AtributosMensaje:
    """Atributos tecnicos detectados en el mensaje del cliente.

    Solo captura lo que se dijo literal. Nunca infiere."""

    pulgadas: Optional[float] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    ram_gb_min: Optional[int] = None


class ExtractorAtributosMensaje:
    """Extrae atributos tecnicos (pulgadas, panel, resolucion) que el cliente
    menciona en lenguaje natural, para persistirlos en el perfil y mantener
    continuidad entre turnos.

    Ejemplo: 'quiero una TV de 85 pulgadas OLED en 4K' →
      AtributosMensaje(pulgadas=85, tipo_panel='OLED', resolucion='4K')

    Estrategia paralela a la del ingestor: regex deterministas, sin LLM. La
    idea es que el perfil conserve el 'contexto tecnico' que el cliente dio
    en un turno para que el siguiente turno no lo pierda."""

    _RAM_VALIDOS = frozenset([4, 8, 12, 16, 24, 32, 48, 64])
    _RX_RAM_A = re.compile(r"\b(\d+)\s*gb\s+(?:de\s+)?ram\b", re.IGNORECASE)
    _RX_RAM_B = re.compile(r"\bram\s+(?:de\s+)?(\d+)\s*gb\b", re.IGNORECASE)

    _RX_PULGADAS = re.compile(
        r"(?<![\d,.])(\d{1,3}(?:[.,]\d)?)\s*(?:\"|pulgadas?|inch(?:es)?|\bin\b)",
        re.IGNORECASE,
    )

    _ORDEN_PANEL = ("MINILED", "QLED", "OLED", "DLED", "LED")
    _RX_PANEL = re.compile(r"\b(miniled|qled|oled|dled|led)\b", re.IGNORECASE)

    _ORDEN_RESOLUCION = ("8K", "4K", "2K", "FHD", "HD")
    _RX_RESOLUCION = re.compile(
        r"\b(8k|4k|2k|full[\s-]?hd|fhd|uhd|hd)\b",
        re.IGNORECASE,
    )

    @classmethod
    def extraer(cls, texto: str) -> AtributosMensaje:
        if not texto:
            return AtributosMensaje()
        return AtributosMensaje(
            pulgadas=cls._pulgadas(texto),
            tipo_panel=cls._panel(texto),
            resolucion=cls._resolucion(texto),
            ram_gb_min=cls._ram_gb(texto),
        )

    @classmethod
    def _ram_gb(cls, texto: str) -> Optional[int]:
        m = cls._RX_RAM_A.search(texto) or cls._RX_RAM_B.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if val in cls._RAM_VALIDOS else None

    @classmethod
    def _pulgadas(cls, texto: str) -> Optional[float]:
        m = cls._RX_PULGADAS.search(texto)
        if not m:
            return None
        valor = float(m.group(1).replace(",", "."))
        return valor if 3 <= valor <= 120 else None

    @classmethod
    def _panel(cls, texto: str) -> Optional[str]:
        encontrados = {m.group(1).upper() for m in cls._RX_PANEL.finditer(texto)}
        for p in cls._ORDEN_PANEL:
            if p in encontrados:
                return p
        return None

    @classmethod
    def _resolucion(cls, texto: str) -> Optional[str]:
        encontrados = {cls._normalizar(m.group(1)) for m in cls._RX_RESOLUCION.finditer(texto)}
        for r in cls._ORDEN_RESOLUCION:
            if r in encontrados:
                return r
        return None

    @staticmethod
    def _normalizar(valor: str) -> str:
        v = valor.upper().replace(" ", "").replace("-", "")
        if v in ("FULLHD", "FHD"):
            return "FHD"
        if v == "UHD":
            return "4K"
        return v
