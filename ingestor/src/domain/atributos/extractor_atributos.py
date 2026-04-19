from __future__ import annotations

import re
from typing import Optional

from .atributos_producto import AtributosProducto


class ExtractorAtributos:
    """Extrae atributos estructurados (pulgadas, GB, litros, color, etc.) del
    nombre y descripcion del producto. Patrones case-insensitive sobre texto
    crudo (con acentos y signos).

    Estrategia: el nombre es la fuente primaria (mas precisa, menos ruido).
    La descripcion actua como fallback para atributos numericos cuando el
    nombre viene truncado (el feed Meta corta titulos a ~65 chars). No se
    usa descripcion para color/panel/resolucion: genera demasiado ruido.

    Solo se extrae lo que aparece LITERAL en el texto; nunca se infiere."""

    _MAX_DESC_CHARS = 1500

    _RX_PULGADAS = re.compile(r'(?<![\d,.])(\d{1,3}(?:[.,]\d)?)\s*"')
    _RX_PULGADAS_TXT = re.compile(
        r'(?<![\d,.])(\d{1,3}(?:[.,]\d)?)\s*(?:pulgadas?|inch(?:es)?|\bin\b)',
        re.IGNORECASE,
    )

    _RX_GB = re.compile(r'(?<!\d)(\d{2,4})\s*gb\b', re.IGNORECASE)
    _RX_TB = re.compile(r'(?<!\d)(\d{1,2})\s*tb\b', re.IGNORECASE)

    _RX_RAM_STORAGE = re.compile(
        r'\((\d{1,3})(?:\+\d{1,3})?\+\s*(\d{2,4})\s*gb\)',
        re.IGNORECASE,
    )

    _RX_RAM_TXT = re.compile(
        r'(?:memoria\s+ram|ram)\s+(?:de\s+|ddr\d\s+)?(\d{1,3})\s*gb\b',
        re.IGNORECASE,
    )
    _RX_STORAGE_TXT = re.compile(
        r'(?:almacenamiento|ssd|hdd|disco(?:\s+duro)?|nvme|emmc)\s*'
        r'(?:[a-z0-9\s]{0,40}?)\s*(?:de\s+)?(\d{2,4})\s*gb\b',
        re.IGNORECASE,
    )

    _RX_LITROS = re.compile(
        r'(?<!\d)(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:lts\.?|lt\.?|litros?|l)\b',
        re.IGNORECASE,
    )

    _RX_KG = re.compile(
        r'(?<!\d)(\d{1,3}(?:[.,]\d)?)\s*kg(?:s\b|\b)',
        re.IGNORECASE,
    )

    _RX_POTENCIA = re.compile(r'(?<!\d)(\d{2,5})\s*w\b(?!\w)', re.IGNORECASE)

    _ORDEN_RESOLUCION = ("8K", "4K", "2K", "FHD", "HD")
    _RX_RESOLUCION = re.compile(
        r'\b(8k|4k|2k|full[\s-]?hd|fhd|uhd|hd)\b',
        re.IGNORECASE,
    )

    _ORDEN_PANEL = ("MINILED", "QLED", "OLED", "DLED", "LED")
    _RX_PANEL = re.compile(r'\b(miniled|qled|oled|dled|led)\b', re.IGNORECASE)

    _RX_PROC_INTEL_CORE = re.compile(
        r'\b(?:intel\s+)?core\s+(i[3579])\b', re.IGNORECASE,
    )
    _RX_PROC_INTEL_MODEL = re.compile(r'\b(i[3579])-\w+', re.IGNORECASE)
    _RX_PROC_INTEL_CORE_NUEVO = re.compile(
        r'\b(?:intel\s+)?core\s+(ultra\s+)?([3579])\b(?!\d)', re.IGNORECASE,
    )
    _RX_PROC_AMD = re.compile(
        r'\bryzen\s+(?:ai\s+)?([3579])\b', re.IGNORECASE,
    )
    _RX_PROC_APPLE = re.compile(
        r'\bapple\s+(m[1-9])\b'
        r'|\bchip\s+(m[1-9])\b'
        r'|\b(m[1-9])\s+(?:pro|max|ultra|chip|w\/)'
        r'|\bmacbook(?:\s+\w+){0,3}\s+(m[1-9])\b',
        re.IGNORECASE,
    )
    _RX_PROC_OTROS = re.compile(
        r'\b(celeron|pentium|xeon|snapdragon|mediatek)\b',
        re.IGNORECASE,
    )

    _COLORES = (
        "negro", "blanco", "gris", "plata", "silver", "dorado", "oro",
        "rojo", "azul", "verde", "amarillo", "rosa", "rosado", "beige",
        "celeste", "turquesa", "morado", "violeta", "cafe", "marron",
        "cobre", "cromo", "crema", "perla", "titanio", "grafito", "inox",
    )
    _RX_COLOR = re.compile(
        r'\bcolor\s+(' + "|".join(_COLORES) + r')\b', re.IGNORECASE,
    )
    _RX_COLOR_SIMPLE = re.compile(
        r'\b(' + "|".join(_COLORES) + r')\b', re.IGNORECASE,
    )

    @classmethod
    def extraer(cls, nombre: str, descripcion: Optional[str] = None) -> AtributosProducto:
        """Extrae todos los atributos detectables. Nombre primario, descripcion fallback."""
        if not nombre:
            return AtributosProducto()
        n = nombre.strip()
        d = (descripcion or "").strip()[: cls._MAX_DESC_CHARS]
        return AtributosProducto(
            pulgadas=cls.pulgadas(n) or cls.pulgadas(d),
            capacidad_gb=cls.capacidad_gb(n) or cls.capacidad_gb(d),
            ram_gb=cls.ram_gb(n) or cls.ram_gb(d),
            capacidad_litros=cls.capacidad_litros(n) or cls.capacidad_litros(d),
            capacidad_kg=cls.capacidad_kg(n) or cls.capacidad_kg(d),
            potencia_w=cls.potencia_w(n) or cls.potencia_w(d),
            procesador=cls.procesador(n) or cls.procesador(d),
            color=cls.color(n),
            tipo_panel=cls.tipo_panel(n),
            resolucion=cls.resolucion(n),
        )

    @classmethod
    def pulgadas(cls, texto: str) -> Optional[float]:
        if not texto:
            return None
        m = cls._RX_PULGADAS.search(texto) or cls._RX_PULGADAS_TXT.search(texto)
        if not m:
            return None
        valor = float(m.group(1).replace(",", "."))
        if valor < 3 or valor > 120:
            return None
        return valor

    @classmethod
    def capacidad_gb(cls, texto: str) -> Optional[int]:
        if not texto:
            return None
        tb = cls._RX_TB.search(texto)
        if tb:
            return int(tb.group(1)) * 1024
        ram_storage = cls._RX_RAM_STORAGE.search(texto)
        if ram_storage:
            return int(ram_storage.group(2))
        storage_txt = cls._RX_STORAGE_TXT.search(texto)
        if storage_txt:
            return int(storage_txt.group(1))
        candidatos = cls._RX_GB.findall(texto)
        if not candidatos:
            return None
        return max(int(v) for v in candidatos)

    @classmethod
    def ram_gb(cls, texto: str) -> Optional[int]:
        if not texto:
            return None
        m = cls._RX_RAM_STORAGE.search(texto)
        if m:
            ram = int(m.group(1))
            return ram if 1 <= ram <= 256 else None
        m = cls._RX_RAM_TXT.search(texto)
        if m:
            ram = int(m.group(1))
            return ram if 1 <= ram <= 256 else None
        return None

    @classmethod
    def capacidad_litros(cls, texto: str) -> Optional[float]:
        if not texto:
            return None
        m = cls._RX_LITROS.search(texto)
        if not m:
            return None
        valor = float(m.group(1).replace(",", "."))
        if valor <= 0 or valor > 2000:
            return None
        return valor

    @classmethod
    def capacidad_kg(cls, texto: str) -> Optional[float]:
        if not texto:
            return None
        m = cls._RX_KG.search(texto)
        if not m:
            return None
        valor = float(m.group(1).replace(",", "."))
        if valor <= 0 or valor > 500:
            return None
        return valor

    @classmethod
    def potencia_w(cls, texto: str) -> Optional[int]:
        if not texto:
            return None
        m = cls._RX_POTENCIA.search(texto)
        if not m:
            return None
        valor = int(m.group(1))
        if valor < 50 or valor > 20000:
            return None
        return valor

    @classmethod
    def procesador(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        m = cls._RX_PROC_INTEL_CORE.search(texto) or cls._RX_PROC_INTEL_MODEL.search(texto)
        if m:
            return m.group(1).lower()
        m = cls._RX_PROC_INTEL_CORE_NUEVO.search(texto)
        if m:
            prefijo = "ultra " if m.group(1) else ""
            return f"core {prefijo}{m.group(2)}"
        m = cls._RX_PROC_AMD.search(texto)
        if m:
            return f"ryzen {m.group(1)}"
        m = cls._RX_PROC_APPLE.search(texto)
        if m:
            return (m.group(1) or m.group(2) or m.group(3) or m.group(4)).lower()
        m = cls._RX_PROC_OTROS.search(texto)
        if m:
            return m.group(1).lower()
        return None

    @classmethod
    def tipo_panel(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        encontrados = {m.group(1).upper() for m in cls._RX_PANEL.finditer(texto)}
        for p in cls._ORDEN_PANEL:
            if p in encontrados:
                return p
        return None

    @classmethod
    def resolucion(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        encontrados = {cls._normalizar_resolucion(m.group(1)) for m in cls._RX_RESOLUCION.finditer(texto)}
        for r in cls._ORDEN_RESOLUCION:
            if r in encontrados:
                return r
        return None

    @staticmethod
    def _normalizar_resolucion(valor: str) -> str:
        v = valor.upper().replace(" ", "").replace("-", "")
        if v in ("FULLHD", "FHD", "UHD"):
            return "FHD" if v in ("FULLHD", "FHD") else "4K"
        return v

    @classmethod
    def color(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        m = cls._RX_COLOR.search(texto)
        if m:
            return cls._canonizar_color(m.group(1).lower())
        m = cls._RX_COLOR_SIMPLE.search(texto)
        if m:
            return cls._canonizar_color(m.group(1).lower())
        return None

    @staticmethod
    def _canonizar_color(c: str) -> str:
        equivalencias = {
            "silver": "plata",
            "oro": "dorado",
            "rosado": "rosa",
            "marron": "cafe",
            "violeta": "morado",
        }
        return equivalencias.get(c, c)
