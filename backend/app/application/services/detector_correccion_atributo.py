from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CorreccionAtributo:
    """Un atributo corregido detectado en el mensaje."""
    campo: str           # nombre del campo en PerfilSesion / BuscarProductosQuery
    valor: object        # valor nuevo (int, float, bool, str)
    confianza: str       # "alta" | "media"


class DetectorCorreccionAtributo:
    """SRP: detecta correcciones del cliente que referencian atributos
    mencionados sin keywords explícitas.

    Casos cubiertos:
      - "dije 256gb"  → ssd_gb_min=256
      - "dije desde 256gb" → ssd_gb_min=256
      - "no, 16gb"  + perfil tiene ram=8 → ram_gb_min=16
      - "o sea con NFC" → nfc=True
      - "quiero android" → sistema_operativo=Android
    """

    _SSD_VALIDOS = frozenset([32, 64, 128, 256, 512, 1024, 2048])
    _RAM_VALIDOS = frozenset([4, 8, 12, 16, 24, 32, 48, 64])

    # "dije (desde|al menos|mínimo|por lo menos)? 256gb / 512gb ..."
    _RX_CORRECCION_GB = re.compile(
        r"\b(?:dije|digo|era|son|puse|quiero|necesito)\s+"
        r"(?:desde\s+|al?\s+menos\s+|m[íi]nimo\s+|por\s+lo\s+menos\s+)?"
        r"(?:de\s+)?(\d{2,4})\s*(?:gb|g)\b",
        re.IGNORECASE,
    )
    # "no, 256gb" / "o sea 256gb" / "me refería a 256gb"
    _RX_CORRECCION_GB_2 = re.compile(
        r"\b(?:no[,\s]+|o\s+sea[,\s]+|me\s+ref[eí]r[íi]a\s+a[,\s]+)"
        r"(?:de\s+)?(\d{2,4})\s*(?:gb|g)\b",
        re.IGNORECASE,
    )
    # Corrección de RAM explícita: "dije 16 ram" / "son 16 de ram"
    _RX_CORRECCION_RAM = re.compile(
        r"\b(?:dije|digo|era|son)\s+(\d+)\s*(?:gb\s+)?(?:de\s+)?(?:ram|memoria|ran)\b",
        re.IGNORECASE,
    )
    # Corrección de hz: "dije 120hz" / "necesito 144hz"
    _RX_CORRECCION_HZ = re.compile(
        r"\b(?:dije|digo|era|quiero|necesito)\s+(\d{2,3})\s*hz\b",
        re.IGNORECASE,
    )
    # Booleanos: "o sea con NFC", "dije con bluetooth", "necesito NFC"
    _BOOL_PATRONES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("nfc",               (r"\bnfc\b",)),
        ("usb_c",             (r"\busb[\s-]?c\b", r"\btype[\s-]?c\b", r"\btipo\s+c\b")),
        ("bluetooth_incluido", (r"\bbluetooth\b", r"\bbt\b")),
        ("hdmi_2_1",          (r"\bhdmi\s*2\.1\b",)),
        ("soporta_5g",        (r"\b5\s*g\b",)),
        ("inverter",          (r"\binverter\b",)),
        ("no_frost",          (r"\bno\s*frost\b",)),
        ("smart_tv",          (r"\bsmart\s*tv\b",)),
        ("wifi_incluido",     (r"\bwi[\s-]?fi\b",)),
    )
    _COMPILED_BOOLS = tuple(
        (campo, tuple(re.compile(p, re.IGNORECASE) for p in patrones))
        for campo, patrones in _BOOL_PATRONES
    )
    # Prefijo de corrección/aclaración
    _RX_PREFIJO = re.compile(
        r"\b(?:o\s+sea[,\s]+|dije[,\s]+|me\s+ref[eé]r[íi]a[,\s]+|"
        r"quiero\s+decir[,\s]+|es\s+decir[,\s]+|"
        r"con\s+|que\s+tenga\s+|que\s+sea\s+)",
        re.IGNORECASE,
    )
    # SO: "quiero android" / "dije windows"
    _SO_MAP = {
        "android": "Android", "ios": "iOS", "iphone": "iOS",
        "windows": "Windows", "win10": "Windows", "win11": "Windows",
        "macos": "macOS", "mac os": "macOS", "macbook": "macOS",
        "chromeos": "ChromeOS", "chromebook": "ChromeOS",
        "linux": "Linux", "ubuntu": "Linux",
        "freedos": "FreeDOS", "free dos": "FreeDOS",
    }
    _RX_SO = re.compile(
        r"\b(?:dije|digo|quiero|era|necesito)\s+(?:con\s+)?"
        r"(android|ios|iphone|windows|win10|win11|macos|mac\s+os|macbook|"
        r"chromeos|chromebook|linux|ubuntu|freedos|free\s+dos)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, mensaje: str, perfil_campos: dict | None = None) -> list[CorreccionAtributo]:
        """Detecta correcciones en el mensaje. perfil_campos es el contexto actual
        del perfil para resolver ambigüedades (ram vs ssd cuando ambos son posibles)."""
        correcciones: list[CorreccionAtributo] = []
        correcciones.extend(cls._correccion_gb(mensaje, perfil_campos or {}))
        correcciones.extend(cls._correccion_ram_explicita(mensaje))
        correcciones.extend(cls._correccion_hz(mensaje))
        correcciones.extend(cls._correccion_bools(mensaje))
        correcciones.extend(cls._correccion_so(mensaje))
        return correcciones

    @classmethod
    def _correccion_gb(cls, texto: str, perfil: dict) -> list[CorreccionAtributo]:
        m = cls._RX_CORRECCION_GB.search(texto) or cls._RX_CORRECCION_GB_2.search(texto)
        if not m:
            return []
        val = int(m.group(1))
        if val not in cls._SSD_VALIDOS or val < 128:
            return []
        # Heurística: si el perfil ya tiene ram_gb_min y el valor es RAM válido también,
        # preferir ssd_gb_min (más común en correcciones de storage).
        campo = "capacidad_gb_min"
        return [CorreccionAtributo(campo=campo, valor=val, confianza="alta")]

    @classmethod
    def _correccion_ram_explicita(cls, texto: str) -> list[CorreccionAtributo]:
        m = cls._RX_CORRECCION_RAM.search(texto)
        if not m:
            return []
        val = int(m.group(1))
        if val not in cls._RAM_VALIDOS:
            return []
        return [CorreccionAtributo(campo="ram_gb_min", valor=val, confianza="alta")]

    @classmethod
    def _correccion_hz(cls, texto: str) -> list[CorreccionAtributo]:
        m = cls._RX_CORRECCION_HZ.search(texto)
        if not m:
            return []
        val = int(m.group(1))
        hz_validos = frozenset([60, 90, 120, 144, 165, 240])
        if val not in hz_validos:
            return []
        return [CorreccionAtributo(campo="refresh_hz_min", valor=val, confianza="alta")]

    @classmethod
    def _correccion_bools(cls, texto: str) -> list[CorreccionAtributo]:
        if not cls._RX_PREFIJO.search(texto):
            return []
        resultado = []
        for campo, patrones in cls._COMPILED_BOOLS:
            if any(p.search(texto) for p in patrones):
                resultado.append(CorreccionAtributo(campo=campo, valor=True, confianza="media"))
        return resultado

    @classmethod
    def _correccion_so(cls, texto: str) -> list[CorreccionAtributo]:
        m = cls._RX_SO.search(texto)
        if not m:
            return []
        clave = m.group(1).lower().replace(" ", "")
        so = cls._SO_MAP.get(clave)
        if not so:
            return []
        return [CorreccionAtributo(campo="sistema_operativo", valor=so, confianza="alta")]
