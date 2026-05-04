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
    ssd_gb_min: Optional[int] = None
    refresh_hz_min: Optional[int] = None
    bateria_mah_min: Optional[int] = None
    camara_mp_min: Optional[int] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    meses_garantia_min: Optional[int] = None
    capacidad_litros_min: Optional[float] = None
    capacidad_kg_min: Optional[float] = None
    potencia_w_min: Optional[int] = None
    carga_rapida_w_min: Optional[int] = None
    eficiencia_energetica: Optional[str] = None
    tipo_combustible: Optional[str] = None
    tipo_carga_lavadora: Optional[str] = None
    ip_rating: Optional[str] = None
    descuento_pct_min: Optional[float] = None
    # Atributos boolean detectados en el mensaje
    inverter: Optional[bool] = None
    no_frost: Optional[bool] = None
    anc: Optional[bool] = None
    smart_tv: Optional[bool] = None
    hdmi_2_1: Optional[bool] = None
    dolby_atmos: Optional[bool] = None
    dolby_vision: Optional[bool] = None
    hdr: Optional[bool] = None
    bluetooth_incluido: Optional[bool] = None
    wifi_incluido: Optional[bool] = None
    nfc: Optional[bool] = None
    usb_c: Optional[bool] = None
    lector_huella: Optional[bool] = None
    dual_sim: Optional[bool] = None
    tactil: Optional[bool] = None
    convertible: Optional[bool] = None
    plegable: Optional[bool] = None
    portatil: Optional[bool] = None
    inalambrico: Optional[bool] = None
    carga_inalambrica: Optional[bool] = None
    airfryer: Optional[bool] = None
    resistente_agua: Optional[bool] = None
    ip67: Optional[bool] = None
    ip68: Optional[bool] = None
    ipx4: Optional[bool] = None
    tiene_descuento: Optional[bool] = None


class ExtractorAtributosMensaje:
    """Extrae atributos tecnicos (pulgadas, panel, resolucion, RAM, SSD) que el
    cliente menciona en lenguaje natural, para persistirlos en el perfil y
    mantener continuidad entre turnos."""

    _RAM_VALIDOS = frozenset([4, 8, 12, 16, 24, 32, 48, 64])
    _SSD_VALIDOS = frozenset([32, 64, 128, 256, 512, 1024, 2048])

    _RX_RAM_A = re.compile(r"\b(\d+)\s*gb\s+(?:de\s+)?ram\b", re.IGNORECASE)
    _RX_RAM_B = re.compile(r"\bram\s+(?:de\s+)?(\d+)\s*gb\b", re.IGNORECASE)

    _RX_SSD_A = re.compile(
        r"\b(\d+)\s*(gb|tb)\s+(?:de\s+)?(?:ssd|almacenamiento|disco|storage|nvme|sata)\b",
        re.IGNORECASE,
    )
    _RX_SSD_B = re.compile(
        r"\b(?:ssd|almacenamiento|disco|storage|nvme)\s+(?:de\s+)?(\d+)\s*(gb|tb)\b",
        re.IGNORECASE,
    )
    _RX_SSD_C = re.compile(
        r"\bm[íi]nimo\s+(\d+)\s*(gb|tb)\s+(?:de\s+)?(?:ssd|almacenamiento|disco)\b",
        re.IGNORECASE,
    )

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

    _HZ_VALIDOS = frozenset([60, 90, 120, 144, 165, 240])
    # Requiere "hz" explícito para no confundir con precios o medidas.
    # Captura "120hz", "144 hz", "120Hz", pero NO "120" solo.
    _RX_HZ = re.compile(r"\b(\d{2,3})\s*hz\b", re.IGNORECASE)

    # Smartphone batería: "5000mah", "batería de 5000", "5,000 mAh"
    _RX_BATERIA_MAH = re.compile(r"\b(\d{4,6})\s*mah\b", re.IGNORECASE)
    _RX_BATERIA_CTX = re.compile(
        r"\bbater[íi]a\s+(?:de\s+)?(\d{4,6})\b", re.IGNORECASE
    )

    # Cámara: "108MP", "camara de 50 mp", "50 megapixeles"
    _RX_CAMARA = re.compile(
        r"\b(\d{1,3})\s*(?:mp|megap[íi]xeles?|megapixels?)\b", re.IGNORECASE
    )

    # Carga rápida: "65W carga rapida", "carga rapida de 33W". Dos regex
    # separados (uno antes, uno después del número) para mantener complejidad
    # bajo el límite del linter.
    _RX_CARGA_W_PRE = re.compile(
        r"\bcarga\s+r[áa]pida\s+(?:de\s+)?(\d{2,3})\s*w?\b", re.IGNORECASE
    )
    _RX_CARGA_W_POS = re.compile(
        r"\b(\d{2,3})\s*w\s+carga\s+r[áa]pida\b", re.IGNORECASE
    )

    # 5G: "5g", "soporta 5g", "que sea 5g"
    _RX_5G = re.compile(r"\b5\s*g\b", re.IGNORECASE)

    # Sistema operativo
    _RX_ANDROID = re.compile(r"\bandroid\b", re.IGNORECASE)
    _RX_IOS = re.compile(r"\bios\b|\biphone\b|\bipad\b|\bipados\b", re.IGNORECASE)
    _RX_WINDOWS = re.compile(r"\bwindows\b|\bwin\s*1[01]\b", re.IGNORECASE)
    _RX_MACOS = re.compile(r"\bmac\s*os\b|\bmacbook\b|\bmacos\b", re.IGNORECASE)
    _RX_CHROMEOS = re.compile(r"\bchrome\s*os\b|\bchromebook\b", re.IGNORECASE)
    _RX_LINUX = re.compile(r"\blinux\b|\bubuntu\b", re.IGNORECASE)
    _RX_FREEDOS = re.compile(r"\bfree\s*dos\b|\bsin\s+sistema\s+operativo\b", re.IGNORECASE)

    # Garantía: "12 meses garantía", "garantía de 2 años"
    _RX_GARANTIA_MESES = re.compile(
        r"\bgarant[íi]a\s+(?:de\s+|por\s+)?(\d{1,2})\s*meses?\b", re.IGNORECASE
    )
    _RX_GARANTIA_ANIOS = re.compile(
        r"\bgarant[íi]a\s+(?:de\s+|por\s+)?(\d{1,2})\s*a[ñn]os?\b", re.IGNORECASE
    )

    # Litros: "420L", "300 litros"
    _RX_LITROS = re.compile(
        r"\b(\d{2,4})\s*(?:l|lts?|litros?)\b", re.IGNORECASE
    )
    # Kilos: "12kg", "8 kilos", "10.5 kg"
    _RX_KG = re.compile(
        r"\b(\d{1,2}(?:[.,]\d)?)\s*(?:kg|kilos?)\b", re.IGNORECASE
    )
    # Watts: "1500w", "potencia de 800 watts"
    _RX_WATTS = re.compile(
        r"\b(\d{2,5})\s*(?:w|watts?|vatios?)\b", re.IGNORECASE
    )

    # Eficiencia energética: A++, A+, A, B, C. Requiere prefijo de contexto
    # explícito para evitar matchear letras sueltas en cualquier mensaje.
    _RX_EFICIENCIA = re.compile(
        r"\b(?:eficiencia(?:\s+energ[ée]tica)?|clase|etiqueta)\s+(a\+\+|a\+|a|b|c|d)\b",
        re.IGNORECASE,
    )

    # Combustible cocinas
    _RX_GAS = re.compile(r"\b(?:a\s+)?gas\b(?!\s*(?:tro|olin))", re.IGNORECASE)
    _RX_INDUCCION = re.compile(r"\binducci[óo]n\b", re.IGNORECASE)
    _RX_ELECTRICA = re.compile(r"\bel[ée]ctric[ao]s?\b", re.IGNORECASE)

    # Tipo carga lavadora
    _RX_FRONTAL = re.compile(r"\bcarga\s+frontal\b|\bfrontal\b", re.IGNORECASE)
    _RX_SUPERIOR = re.compile(r"\bcarga\s+superior\b|\bsuperior\b", re.IGNORECASE)

    # IP rating
    _RX_IP_RATING = re.compile(r"\b(ip\s*\d{2}|ipx\d)\b", re.IGNORECASE)

    # Descuento % (dos regex separados: número antes vs número después).
    _RX_DESCUENTO_PRE = re.compile(
        r"\b(\d{1,2})\s*%\s*(?:de\s+)?descuento\b", re.IGNORECASE
    )
    _RX_DESCUENTO_POS = re.compile(
        r"\bdescuento\s+de\s+(\d{1,2})\s*%", re.IGNORECASE
    )

    # Mapeo bool simple: keyword → atributo boolean (cuando aparece la palabra
    # afirmativamente en el mensaje → True). Las negaciones no se intentan aquí
    # para evitar falsos positivos; el LLM las maneja en su tool call.
    _BOOLS_KEYWORDS = (
        ("inverter",          (r"\binverter\b",)),
        ("no_frost",          (r"\bno\s*frost\b", r"\bnofrost\b")),
        ("anc",               (r"\banc\b", r"\bnoise\s+cancel", r"\bcancelaci[óo]n\s+de\s+ruido\b")),
        ("smart_tv",          (r"\bsmart\s*tv\b", r"\bgoogle\s*tv\b", r"\bandroid\s*tv\b", r"\bweb\s*os\b", r"\btizen\b")),
        ("hdmi_2_1",          (r"\bhdmi\s*2\.1\b",)),
        ("dolby_atmos",       (r"\bdolby\s+atmos\b",)),
        ("dolby_vision",      (r"\bdolby\s+vision\b",)),
        ("hdr",               (r"\bhdr\b",)),
        ("bluetooth_incluido", (r"\bbluetooth\b", r"\bbt\b")),
        ("wifi_incluido",     (r"\bwi[\s-]?fi\b",)),
        ("nfc",               (r"\bnfc\b",)),
        ("usb_c",             (r"\busb[\s-]?c\b", r"\btype[\s-]?c\b", r"\btipo\s+c\b")),
        ("lector_huella",     (r"\bhuella\b", r"\bfingerprint\b")),
        ("dual_sim",          (r"\bdual\s+sim\b", r"\bdoble\s+sim\b")),
        ("tactil",            (r"\bt[áa]ctil\b", r"\btouch\s*screen\b")),
        ("convertible",       (r"\bconvertible\b", r"\b2\s+en\s+1\b", r"\b2-in-1\b")),
        ("plegable",          (r"\bplegable\b", r"\bfoldable\b")),
        ("portatil",          (r"\bport[áa]til\b",)),
        ("inalambrico",       (r"\binal[áa]mbric[oa]\b", r"\bwireless\b")),
        ("carga_inalambrica", (r"\bcarga\s+inal[áa]mbrica\b", r"\bwireless\s+charging\b")),
        ("airfryer",          (r"\bair\s*fryer\b", r"\bfreidora\s+de\s+aire\b")),
        ("resistente_agua",   (r"\bresistente\s+al\s+agua\b", r"\bwaterproof\b")),
    )
    _COMPILED_BOOLS = tuple(
        (campo, tuple(re.compile(p, re.IGNORECASE) for p in patrones))
        for campo, patrones in _BOOLS_KEYWORDS
    )

    @classmethod
    def extraer(cls, texto: str) -> AtributosMensaje:
        if not texto:
            return AtributosMensaje()
        bools = cls._extraer_booleanos(texto)
        return AtributosMensaje(
            pulgadas=cls._pulgadas(texto),
            tipo_panel=cls._panel(texto),
            resolucion=cls._resolucion(texto),
            ram_gb_min=cls._ram_gb(texto),
            ssd_gb_min=cls._ssd_gb(texto),
            refresh_hz_min=cls._refresh_hz(texto),
            bateria_mah_min=cls._bateria_mah(texto),
            camara_mp_min=cls._camara_mp(texto),
            soporta_5g=cls._soporta_5g(texto),
            sistema_operativo=cls._sistema_operativo(texto),
            meses_garantia_min=cls._meses_garantia(texto),
            capacidad_litros_min=cls._litros(texto),
            capacidad_kg_min=cls._kg(texto),
            potencia_w_min=cls._watts(texto),
            carga_rapida_w_min=cls._carga_rapida(texto),
            eficiencia_energetica=cls._eficiencia(texto),
            tipo_combustible=cls._combustible(texto),
            tipo_carga_lavadora=cls._tipo_carga_lavadora(texto),
            ip_rating=cls._ip_rating(texto),
            descuento_pct_min=cls._descuento_pct(texto),
            tiene_descuento=cls._tiene_descuento(texto),
            ip67=bools.get("ip67"),
            ip68=bools.get("ip68"),
            ipx4=bools.get("ipx4"),
            **bools.get("_extra", {}),
        )

    @classmethod
    def _ram_gb(cls, texto: str) -> Optional[int]:
        m = cls._RX_RAM_A.search(texto) or cls._RX_RAM_B.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if val in cls._RAM_VALIDOS else None

    @classmethod
    def _ssd_gb(cls, texto: str) -> Optional[int]:
        for rx in (cls._RX_SSD_A, cls._RX_SSD_B, cls._RX_SSD_C):
            m = rx.search(texto)
            if not m:
                continue
            val = int(m.group(1))
            unit = m.group(2).lower()
            if unit == "tb":
                val *= 1024
            if val in cls._SSD_VALIDOS:
                return val
        return None

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
        encontrados = set()
        for m in cls._RX_RESOLUCION.finditer(texto):
            raw = m.group(1).upper().replace(" ", "").replace("-", "")
            if raw in ("FULLHD", "FHD", "UHD"):
                encontrados.add("FHD")
            else:
                encontrados.add(raw)
        for r in cls._ORDEN_RESOLUCION:
            if r in encontrados:
                return r
        return None

    @classmethod
    def _refresh_hz(cls, texto: str) -> Optional[int]:
        for m in cls._RX_HZ.finditer(texto):
            val = int(m.group(1))
            if val in cls._HZ_VALIDOS:
                return val
        return None

    @classmethod
    def _bateria_mah(cls, texto: str) -> Optional[int]:
        m = cls._RX_BATERIA_MAH.search(texto) or cls._RX_BATERIA_CTX.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if 1000 <= val <= 50000 else None

    @classmethod
    def _camara_mp(cls, texto: str) -> Optional[int]:
        m = cls._RX_CAMARA.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if 1 <= val <= 250 else None

    @classmethod
    def _carga_rapida(cls, texto: str) -> Optional[int]:
        m = cls._RX_CARGA_W_PRE.search(texto) or cls._RX_CARGA_W_POS.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if 5 <= val <= 300 else None

    @classmethod
    def _soporta_5g(cls, texto: str) -> Optional[bool]:
        return True if cls._RX_5G.search(texto) else None

    @classmethod
    def _sistema_operativo(cls, texto: str) -> Optional[str]:
        # Orden importa: iOS antes que Android (no se ven mezclados pero por las dudas).
        if cls._RX_IOS.search(texto):
            return "iOS"
        if cls._RX_MACOS.search(texto):
            return "macOS"
        if cls._RX_CHROMEOS.search(texto):
            return "ChromeOS"
        if cls._RX_FREEDOS.search(texto):
            return "FreeDOS"
        if cls._RX_LINUX.search(texto):
            return "Linux"
        if cls._RX_WINDOWS.search(texto):
            return "Windows"
        if cls._RX_ANDROID.search(texto):
            return "Android"
        return None

    @classmethod
    def _meses_garantia(cls, texto: str) -> Optional[int]:
        m = cls._RX_GARANTIA_MESES.search(texto)
        if m:
            return int(m.group(1))
        m = cls._RX_GARANTIA_ANIOS.search(texto)
        if m:
            return int(m.group(1)) * 12
        return None

    @classmethod
    def _litros(cls, texto: str) -> Optional[float]:
        m = cls._RX_LITROS.search(texto)
        if not m:
            return None
        val = float(m.group(1))
        return val if 5 <= val <= 1000 else None

    @classmethod
    def _kg(cls, texto: str) -> Optional[float]:
        m = cls._RX_KG.search(texto)
        if not m:
            return None
        val = float(m.group(1).replace(",", "."))
        return val if 0.5 <= val <= 50 else None

    @classmethod
    def _watts(cls, texto: str) -> Optional[int]:
        m = cls._RX_WATTS.search(texto)
        if not m:
            return None
        val = int(m.group(1))
        return val if 10 <= val <= 30000 else None

    _MAPA_EFICIENCIA = {
        "a++": "A++", "a+": "A+", "a": "A",
        "b": "B", "c": "C", "d": "D",
    }

    @classmethod
    def _eficiencia(cls, texto: str) -> Optional[str]:
        m = cls._RX_EFICIENCIA.search(texto)
        if not m:
            return None
        return cls._MAPA_EFICIENCIA.get(m.group(1).lower())

    @classmethod
    def _combustible(cls, texto: str) -> Optional[str]:
        if cls._RX_INDUCCION.search(texto):
            return "induccion"
        # "estufa de gas", "cocina a gas". Excluir "gasolina" / "gastronomia".
        if cls._RX_GAS.search(texto):
            return "gas"
        # "cocina electrica" — palabra clave fuerte
        if cls._RX_ELECTRICA.search(texto):
            return "electrico"
        return None

    @classmethod
    def _tipo_carga_lavadora(cls, texto: str) -> Optional[str]:
        if cls._RX_FRONTAL.search(texto):
            return "frontal"
        if cls._RX_SUPERIOR.search(texto):
            return "superior"
        return None

    @classmethod
    def _ip_rating(cls, texto: str) -> Optional[str]:
        m = cls._RX_IP_RATING.search(texto)
        if not m:
            return None
        return m.group(1).upper().replace(" ", "")

    @classmethod
    def _descuento_pct(cls, texto: str) -> Optional[float]:
        m = cls._RX_DESCUENTO_PRE.search(texto) or cls._RX_DESCUENTO_POS.search(texto)
        if not m:
            return None
        return float(m.group(1))

    _RX_TIENE_DESCUENTO = re.compile(
        r"\b(?:en\s+oferta|con\s+descuento|rebajad[oa]|liquidaci[oó]n)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _tiene_descuento(cls, texto: str) -> Optional[bool]:
        if cls._descuento_pct(texto) is not None:
            return True
        return True if cls._RX_TIENE_DESCUENTO.search(texto) else None

    @classmethod
    def _extraer_booleanos(cls, texto: str) -> dict:
        """Itera el mapeo _COMPILED_BOOLS y arma el dict de atributos detectados.
        Cada filtro = True solo si encuentra match — None si no aparece (sin
        contradicción explícita)."""
        extra: dict = {}
        for campo, patrones in cls._COMPILED_BOOLS:
            if any(p.search(texto) for p in patrones):
                extra[campo] = True
        # IP rating individual (ip67/ip68/ipx4 como booleans dedicados)
        ip = cls._ip_rating(texto)
        result: dict = {"_extra": extra}
        if ip:
            ip_lower = ip.lower().replace(" ", "")
            if ip_lower == "ip67":
                result["ip67"] = True
            elif ip_lower == "ip68":
                result["ip68"] = True
            elif ip_lower == "ipx4":
                result["ipx4"] = True
        return result
