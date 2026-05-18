from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AtributosExtraidos:
    """Resultado de parsear nombre + descripción de un producto."""
    sku: str
    pulgadas: Optional[float] = None
    ram_gb: Optional[int] = None
    capacidad_gb: Optional[int] = None
    refresh_hz: Optional[int] = None
    bateria_mah: Optional[int] = None
    camara_mp: Optional[int] = None
    potencia_w: Optional[int] = None
    capacidad_kg: Optional[float] = None
    sistema_operativo: Optional[str] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    soporta_5g: Optional[bool] = None
    campos_poblados: list[str] = field(default_factory=list)


class ExtractorAtributosProducto:
    """SRP: extrae atributos estructurados del texto plano (nombre + descripción)
    de un producto cuando sus columnas SQL están vacías.

    No accede a la DB — solo parsea texto. La persistencia la maneja el handler."""

    _RX_PULGADAS = re.compile(r'(\d{1,2}(?:[.,]\d)?)\s*(?:"|pulgadas|pulg)\b', re.IGNORECASE)
    _RX_RAM = re.compile(r'(\d+)\s*gb\s+(?:ram|memoria ram)\b|(?:ram|memoria)\s+(\d+)\s*gb', re.IGNORECASE)
    _RX_SSD_VALIDOS = frozenset([32, 64, 128, 256, 512, 1024, 2048])
    _RX_SSD = re.compile(
        r'(\d{2,4})\s*gb\s+(?:ssd|nvme|emmc|almacenamiento|disco|storage)\b'
        r'|(?:ssd|nvme|emmc|almacenamiento)\s+(?:de\s+)?(\d{2,4})\s*gb',
        re.IGNORECASE,
    )
    _RX_HZ = re.compile(r'(\d{2,3})\s*hz\b', re.IGNORECASE)
    _RX_MAH = re.compile(r'(\d{3,5})\s*mah\b', re.IGNORECASE)
    _RX_MP = re.compile(r'(\d{1,3})\s*mp\b', re.IGNORECASE)
    _RX_WATTS = re.compile(r'(\d{2,5})\s*w\b', re.IGNORECASE)
    _RX_KG = re.compile(r'(\d{1,2}(?:[.,]\d)?)\s*kg\b', re.IGNORECASE)
    _SO_MAP = {
        "android": "Android", "ios": "iOS", "iphone": "iOS",
        "windows": "Windows", "win10": "Windows", "win11": "Windows",
        "macos": "macOS", "macbook": "macOS",
        "chromeos": "ChromeOS", "chromebook": "ChromeOS",
        "linux": "Linux", "ubuntu": "Linux",
        "freedos": "FreeDOS",
    }
    _RX_SO = re.compile(
        r'\b(android|ios|windows|win\s?1[01]|macos|mac\s?os|chromeos|linux|ubuntu|freedos)\b',
        re.IGNORECASE,
    )
    _PANEL_MAP = {
        "oled": "OLED", "amoled": "AMOLED", "qled": "QLED",
        "ips": "IPS", "va": "VA", "tn": "TN", "led": "LED",
    }
    _RX_PANEL = re.compile(
        r'\b(oled|amoled|qled|super\s+amoled|ips|va\b|tn\b|led)\b', re.IGNORECASE
    )
    _RX_RESOLUCION = re.compile(
        r'\b(4k|8k|2k|qhd|fhd|full\s*hd|hd\+|hd|uhd|1080p|1440p|2160p|720p)\b',
        re.IGNORECASE,
    )
    _RX_5G = re.compile(r'\b5g\b', re.IGNORECASE)
    _RESOLUCION_NORM = {
        "4k": "4K", "8k": "8K", "2k": "2K", "qhd": "QHD",
        "fhd": "FHD", "full hd": "FHD", "fullhd": "FHD",
        "hd+": "HD+", "hd": "HD", "uhd": "UHD",
        "1080p": "FHD", "1440p": "QHD", "2160p": "4K", "720p": "HD",
    }

    @classmethod
    def extraer(cls, sku: str, nombre: str, descripcion: str | None = None,
                atributos_texto: str | None = None) -> AtributosExtraidos:
        """Extrae atributos del texto combinado. Solo sobreescribe si el valor
        encontrado tiene alta confianza (el campo objetivo es NULL en la BD)."""
        texto = " ".join(filter(None, [nombre, descripcion, atributos_texto]))
        resultado = AtributosExtraidos(sku=sku)
        cls._extraer_pulgadas(texto, resultado)
        cls._extraer_ram(texto, resultado)
        cls._extraer_ssd(texto, resultado)
        cls._extraer_hz(texto, resultado)
        cls._extraer_mah(texto, resultado)
        cls._extraer_mp(texto, resultado)
        cls._extraer_potencia(texto, resultado)
        cls._extraer_kg(texto, resultado)
        cls._extraer_so(texto, resultado)
        cls._extraer_panel(texto, resultado)
        cls._extraer_resolucion(texto, resultado)
        cls._extraer_5g(texto, resultado)
        return resultado

    @classmethod
    def _extraer_pulgadas(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_PULGADAS.search(texto)
        if m:
            val = float(m.group(1).replace(",", "."))
            if 1 < val < 110:
                r.pulgadas = val
                r.campos_poblados.append("pulgadas")

    @classmethod
    def _extraer_ram(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_RAM.search(texto)
        if m:
            val = int(m.group(1) or m.group(2))
            if val in (2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64):
                r.ram_gb = val
                r.campos_poblados.append("ram_gb")

    @classmethod
    def _extraer_ssd(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_SSD.search(texto)
        if m:
            val = int(m.group(1) or m.group(2))
            if val in cls._RX_SSD_VALIDOS:
                r.capacidad_gb = val
                r.campos_poblados.append("capacidad_gb")

    @classmethod
    def _extraer_hz(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_HZ.search(texto)
        if m:
            val = int(m.group(1))
            if val in (48, 50, 60, 90, 100, 120, 144, 165, 240):
                r.refresh_hz = val
                r.campos_poblados.append("refresh_hz")

    @classmethod
    def _extraer_mah(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_MAH.search(texto)
        if m:
            val = int(m.group(1))
            if 500 <= val <= 30000:
                r.bateria_mah = val
                r.campos_poblados.append("bateria_mah")

    @classmethod
    def _extraer_mp(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_MP.search(texto)
        if m:
            val = int(m.group(1))
            if 2 <= val <= 200:
                r.camara_mp = val
                r.campos_poblados.append("camara_mp")

    @classmethod
    def _extraer_potencia(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_WATTS.search(texto)
        if m:
            val = int(m.group(1))
            if 5 <= val <= 30000:
                r.potencia_w = val
                r.campos_poblados.append("potencia_w")

    @classmethod
    def _extraer_kg(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_KG.search(texto)
        if m:
            val = float(m.group(1).replace(",", "."))
            if 0.5 <= val <= 30:
                r.capacidad_kg = val
                r.campos_poblados.append("capacidad_kg")

    @classmethod
    def _extraer_so(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_SO.search(texto)
        if m:
            clave = m.group(1).lower().replace(" ", "")
            so = cls._SO_MAP.get(clave)
            if so:
                r.sistema_operativo = so
                r.campos_poblados.append("sistema_operativo")

    @classmethod
    def _extraer_panel(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_PANEL.search(texto)
        if m:
            clave = m.group(1).lower().replace(" ", "")
            panel = cls._PANEL_MAP.get(clave)
            if panel:
                r.tipo_panel = panel
                r.campos_poblados.append("tipo_panel")

    @classmethod
    def _extraer_resolucion(cls, texto: str, r: AtributosExtraidos) -> None:
        m = cls._RX_RESOLUCION.search(texto)
        if m:
            clave = m.group(1).lower().replace(" ", "")
            res = cls._RESOLUCION_NORM.get(clave, m.group(1).upper())
            r.resolucion = res
            r.campos_poblados.append("resolucion")

    @classmethod
    def _extraer_5g(cls, texto: str, r: AtributosExtraidos) -> None:
        if cls._RX_5G.search(texto):
            r.soporta_5g = True
            r.campos_poblados.append("soporta_5g")
