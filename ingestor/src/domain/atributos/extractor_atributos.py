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

    # ------- SPECS para comparativas (batería, cámara, 5G, refresh, SO, GPU) -----
    # Acepta "5000 mAh", "5,000 mAh", "5.000 mAh"; quita separadores al int().
    _RX_BATERIA = re.compile(r'(?<!\d)(\d{1,3}(?:[.,]\d{3})?|\d{3,5})\s*mAh\b', re.IGNORECASE)
    _RX_CAMARA_PRINCIPAL = re.compile(r'(?<!\d)(\d{1,3})\s*MP\b', re.IGNORECASE)
    _RX_CAMARA_FRONTAL_CONTEXTO = re.compile(r'(?:selfie|frontal|front)', re.IGNORECASE)
    _RX_MP_NUMERO = re.compile(r'(\d{1,3})\s*MP', re.IGNORECASE)
    _RX_5G = re.compile(r'\b5\s?G\b', re.IGNORECASE)
    _RX_REFRESH = re.compile(r'(\d{2,3})\s*Hz\b', re.IGNORECASE)
    _RX_SO = re.compile(
        r'\b(android|ios|windows|webos|tizen|wear\s*os|chromeos)\b', re.IGNORECASE
    )
    _RX_GPU = re.compile(
        r'\b(geforce\s+(?:rtx|gtx)\s+\d{3,4}\w*|radeon\s+\w+|mali-\w+|adreno\s+\d+)\b',
        re.IGNORECASE,
    )

    _MIN_BATERIA_MAH = 500
    _MIN_CAMARA_MP = 2

    @classmethod
    def extraer(cls, nombre: str, descripcion: Optional[str] = None) -> AtributosProducto:
        """Extrae todos los atributos detectables. Nombre primario, descripcion fallback."""
        if not nombre:
            return AtributosProducto()
        n = nombre.strip()
        d = (descripcion or "").strip()[: cls._MAX_DESC_CHARS]
        texto_nd = f"{n} {d}"
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
            bateria_mah=cls.bateria_mah(texto_nd),
            camara_mp=cls.camara_mp(texto_nd),
            camara_frontal_mp=cls.camara_frontal_mp(texto_nd),
            soporta_5g=cls.soporta_5g(texto_nd),
            refresh_hz=cls.refresh_hz(texto_nd),
            sistema_operativo=cls.sistema_operativo(texto_nd),
            gpu=cls.gpu(texto_nd),
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

    @classmethod
    def bateria_mah(cls, texto: str) -> Optional[int]:
        if not texto:
            return None
        m = cls._RX_BATERIA.search(texto)
        if not m:
            return None
        try:
            valor = int(m.group(1).replace(",", "").replace(".", ""))
        except ValueError:
            return None
        return valor if valor >= cls._MIN_BATERIA_MAH else None

    @classmethod
    def camara_mp(cls, texto: str) -> Optional[int]:
        """MP más alto que aparezca en el texto, asumiendo que esa es la
        cámara principal (regla del vendedor: si el texto cita 200 MP y
        48 MP, la principal es la de 200)."""
        if not texto:
            return None
        candidatos = [int(m) for m in cls._RX_CAMARA_PRINCIPAL.findall(texto)]
        validos = [c for c in candidatos if c >= cls._MIN_CAMARA_MP]
        return max(validos) if validos else None

    @classmethod
    def camara_frontal_mp(cls, texto: str) -> Optional[int]:
        """Busca un 'N MP' dentro de 40 chars de 'selfie/frontal/front'."""
        if not texto:
            return None
        for ctx in cls._RX_CAMARA_FRONTAL_CONTEXTO.finditer(texto):
            inicio = max(0, ctx.start() - 40)
            fin = min(len(texto), ctx.end() + 40)
            ventana = texto[inicio:fin]
            mp = cls._RX_MP_NUMERO.search(ventana)
            if mp:
                valor = int(mp.group(1))
                if valor >= cls._MIN_CAMARA_MP:
                    return valor
        return None

    @classmethod
    def soporta_5g(cls, texto: str) -> Optional[bool]:
        if not texto:
            return None
        return True if cls._RX_5G.search(texto) else None

    @classmethod
    def refresh_hz(cls, texto: str) -> Optional[int]:
        if not texto:
            return None
        # Mayor Hz del texto (descartar Hz ≤ 30 como "ruido" típico)
        candidatos = [int(m) for m in cls._RX_REFRESH.findall(texto) if int(m) >= 40]
        return max(candidatos) if candidatos else None

    @classmethod
    def sistema_operativo(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        m = cls._RX_SO.search(texto)
        return m.group(1).lower() if m else None

    @classmethod
    def gpu(cls, texto: str) -> Optional[str]:
        if not texto:
            return None
        m = cls._RX_GPU.search(texto)
        return m.group(1) if m else None
