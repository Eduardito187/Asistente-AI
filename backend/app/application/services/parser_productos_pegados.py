from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ProductoPegado:
    """Producto que el cliente pego en el chat (no necesariamente del
    catalogo). Atributos None = no detectado en el texto. NO se inventa."""

    raw: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    cpu: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    pulgadas: Optional[float] = None
    precio_bob: Optional[float] = None
    sistema_operativo: Optional[str] = None
    gpu: Optional[str] = None

    @property
    def es_util(self) -> bool:
        """Tiene al menos marca o modelo + algun spec/precio para que valga
        la pena listar/comparar."""
        identidad = bool(self.marca or self.modelo)
        spec = any([
            self.cpu, self.ram_gb, self.storage_gb, self.precio_bob, self.pulgadas,
        ])
        return identidad and spec


@dataclass(frozen=True)
class ListadoPegado:
    productos: list[ProductoPegado] = field(default_factory=list)

    def vacio(self) -> bool:
        return len(self.productos) == 0


class ParserProductosPegados:
    """SRP: detecta cuando el cliente pego una lista de productos con
    sus specs (formato libre, una por linea o separados por comas) y los
    extrae a `ProductoPegado` para comparacion sin necesidad de buscar
    cada uno en catalogo.

    Caso de uso del feedback (2026-05-07): el cliente pega
        asus tuf f16 i5 16 ram 512 bs 10699 freedos
        asus x515 i7 16 ram 512 bs 10799
        hp ryzen 7 16 ram 512 bs 7499
    El bot decia 'no tenemos similares' cuando el cliente NO pedia
    catalogo, pedia comparar entre esos.

    Heuristicas:
    - Cada linea no vacia con >= 4 tokens y >= 2 senales (marca|cpu|ram|
      storage|precio) cuenta como un producto pegado.
    - Si hay >= 2 lineas validas, devolvemos ListadoPegado no-vacio."""

    _MARCAS_CONOCIDAS = (
        "asus", "hp", "lenovo", "dell", "acer", "msi", "samsung", "apple",
        "macbook", "huawei", "xiaomi", "lg", "alienware", "gigabyte", "razer",
        "toshiba", "hisense", "tcl", "sony", "panasonic", "philips",
        "tecno", "infinix", "motorola", "oppo", "vivo", "honor", "realme",
        "google", "pixel", "nokia",
    )

    # CPU: tier (i5/i7/ryzen 5/ryzen 7/m1/m2/m3/m4/celeron/pentium). Capturamos
    # solo el tier base — el sufijo opcional ('-13420H' o '7-7445HS') puede
    # venir pero NO permitimos capturar otro numero standalone que confunda
    # con RAM/storage (ej. 'ryzen 7 16' debe extraer solo 'ryzen 7').
    _CPUS_RX = re.compile(
        r"\b(?:intel\s+)?(?:core\s+)?i[3579](?:\s*-\s*\d{2,5}[a-z]{0,3})?\b"
        r"|\b(?:amd\s+)?ryzen\s*[3579](?:\s*-\s*\d{2,5}[a-z]{0,3})?\b"
        r"|\b(?:m1|m2|m3|m4)(?:\s+(?:pro|max|ultra))?\b"
        r"|\b(?:celeron|pentium|xeon|atom)\b"
        r"|\bsnapdragon\s*\d+\b|\bmediatek\b|\bdimensity\s*\d+\b"
        r"|\bapple\s+a\d+\b",
        re.IGNORECASE,
    )

    # "16 ram", "16gb", "ram 16gb", "16 de ram", "16GB" sin keyword (lookahead)
    _RAM_RX = re.compile(
        r"\b(\d{1,3})\s*(?:gb)?\s+(?:de\s+)?(?:ram|memoria)\b"
        r"|\bram\s+(?:de\s+)?(\d{1,3})\s*(?:gb)?\b"
        r"|\b(4|8|12|16|24|32|48|64)\s*gb\b(?!\s*(?:ssd|nvme|emmc|disco|sata))",
        re.IGNORECASE,
    )

    # "512", "512gb", "1tb", "512 ssd", "512SSD" (sin espacio).
    _STORAGE_RX = re.compile(
        r"\b(\d{2,4})\s*(?:gb|g)?\s+(?:ssd|disco|almacenamiento|nvme|sata|emmc)\b"
        r"|\b(?:ssd|disco|almacenamiento|nvme)\s+(?:de\s+)?(\d{2,4})\s*(?:gb|g)?\b"
        r"|\b(\d{1,2})\s*tb\b"
        r"|\b(\d{2,4})\s*(?:gb|g)?\s*(?:ssd|nvme|emmc)\b",
        re.IGNORECASE,
    )

    # Precios en BOB: "bs 10699", "10699 bs", "10.699", "Bs. 8000".
    # Forzamos minimo 4 digitos (>= 1000 Bs) para no confundir con RAM/storage
    # (no hay productos del catalogo Dismac < Bs 1000 en categorias relevantes).
    _PRECIO_RX = re.compile(
        r"\bbs\.?\s+(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d{4,})\b"
        r"|\b(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d{4,})\s*bs\b",
        re.IGNORECASE,
    )

    _PULGADAS_RX = re.compile(
        r"\b(\d{1,2}(?:[.,]\d)?)\s*(?:\"|pulgadas?|inch(?:es)?|\bin\b)\b",
        re.IGNORECASE,
    )

    _SO_RX = re.compile(
        r"\b(freedos|free\s*dos|windows\s*1?[01]?|win\s*1?[01]?|"
        r"linux|chrome\s*os|chromebook|macos|mac\s*os)\b",
        re.IGNORECASE,
    )

    _GPU_RX = re.compile(
        r"\b(?:rtx|gtx|geforce|radeon|rx\s*\d+|nvidia)\s*\w*\b",
        re.IGNORECASE,
    )

    # Regex para detectar dos valores GB en la misma linea (ej. "16GB 512GB"),
    # para inferir RAM (valor <= 64) cuando no aparece keyword "ram/memoria".
    _RX_DOS_GB = re.compile(r"\b(\d{1,3})\s*gb\b.*?\b(\d{2,4})\s*gb\b", re.IGNORECASE)

    @classmethod
    def parsear(cls, mensaje: str) -> ListadoPegado:
        if not mensaje:
            return ListadoPegado()
        # Soporta lineas por \n o ;, y tambien productos separados por " / "
        # (con espacios) en una sola linea. NO reemplazamos "/" sin espacios
        # para no romper formatos como "i5/16GB/512SSD".
        mensaje_norm = mensaje.replace(" / ", "\n")
        # Preprocesamiento: separar productos en lista CSV por marca conocida
        # ej. "Asus TUF Bs 10699, HP Pavilion Bs 8500" → dos lineas
        mensaje_norm = cls._separar_productos_por_marca(mensaje_norm)
        lineas = re.split(r"[\n;]+", mensaje_norm)
        productos: list[ProductoPegado] = []
        for linea in lineas:
            linea = linea.strip(" -•*\t")
            if len(linea.split()) < 4:
                continue
            prod = cls._parsear_linea(linea)
            if prod and prod.es_util:
                productos.append(prod)
        # Solo lo consideramos un "listado pegado" si hay >= 2 productos
        # con specs — un solo producto suele ser una pregunta normal.
        if len(productos) < 2:
            return ListadoPegado()
        return ListadoPegado(productos=productos)

    @classmethod
    def _separar_productos_por_marca(cls, texto: str) -> str:
        """Convierte lista CSV en lineas separadas cuando cada elemento empieza
        con una marca conocida.

        'Asus TUF Bs 10699, HP Pavilion Bs 8500, Lenovo i5 Bs 9200'
        -> 'Asus TUF Bs 10699\nHP Pavilion Bs 8500\nLenovo i5 Bs 9200'

        Solo reemplaza la coma+espacio que precede a una marca; las comas
        internas (ej. "1,024 GB") no se tocan."""
        alternacion = "|".join(re.escape(m) for m in cls._MARCAS_CONOCIDAS)
        patron = re.compile(
            rf",\s+({alternacion})\b",
            re.IGNORECASE,
        )
        return patron.sub(r"\n\1", texto)

    @classmethod
    def _parsear_linea(cls, linea: str) -> ProductoPegado | None:
        marca = cls._marca(linea)
        cpu = cls._captura_primera(cls._CPUS_RX, linea)
        ram = cls._numero_ram(linea)
        storage = cls._numero_storage(linea)
        precio = cls._numero_precio(linea)
        pulgadas = cls._numero_pulgadas(linea)
        so = cls._captura_primera(cls._SO_RX, linea)
        gpu = cls._captura_primera(cls._GPU_RX, linea)
        modelo = cls._modelo(linea, marca)
        return ProductoPegado(
            raw=linea,
            marca=marca,
            modelo=modelo,
            cpu=cpu,
            ram_gb=ram,
            storage_gb=storage,
            pulgadas=pulgadas,
            precio_bob=precio,
            sistema_operativo=so,
            gpu=gpu,
        )

    @classmethod
    def _marca(cls, linea: str) -> str | None:
        bajo = linea.lower()
        for marca in cls._MARCAS_CONOCIDAS:
            if re.search(rf"\b{re.escape(marca)}\b", bajo):
                return marca.capitalize()
        return None

    @classmethod
    def _modelo(cls, linea: str, marca: str | None) -> str | None:
        """Heuristica: tras la marca, la siguiente palabra alfanumerica que
        NO sea CPU/spec es el modelo. Ej: 'asus tuf f16 i5...' -> 'tuf f16'."""
        if not marca:
            return None
        m = re.search(
            rf"\b{re.escape(marca.lower())}\b\s+([\w][\w\s\-]{{1,30}}?)\s+"
            r"(?:i[357]|ryzen|core|m[1234]|celeron|\d+\s*gb|\d+\s*ram)",
            linea.lower(),
        )
        if not m:
            return None
        modelo = m.group(1).strip()
        return modelo.upper() if len(modelo) <= 8 else modelo.title()

    @staticmethod
    def _captura_primera(rx: re.Pattern, texto: str) -> str | None:
        m = rx.search(texto)
        if not m:
            return None
        return m.group(0).strip()

    _RAM_VALIDOS = frozenset((4, 8, 12, 16, 24, 32, 48, 64))

    @classmethod
    def _numero_ram(cls, linea: str) -> int | None:
        m = cls._RAM_RX.search(linea)
        if m:
            valor = m.group(1) or m.group(2) or m.group(3)
            try:
                v = int(valor)
                return v if v in cls._RAM_VALIDOS else None
            except (ValueError, TypeError):
                pass
        # Desambiguacion: si hay dos valores GB en la linea (ej. "16GB 512GB"),
        # el menor (<= 64) es RAM y el mayor es storage. Solo aplica si no hay
        # keyword "ram/memoria" (ya cubierto arriba).
        m2 = cls._RX_DOS_GB.search(linea)
        if m2:
            try:
                a, b = int(m2.group(1)), int(m2.group(2))
                menor, mayor = (a, b) if a <= b else (b, a)
                if menor in cls._RAM_VALIDOS and mayor >= 128:
                    return menor
            except (ValueError, TypeError):
                pass
        return None

    _SSD_VALIDOS_TOTAL = frozenset((32, 64, 128, 256, 512, 1024, 2048))
    _SSD_VALIDOS_FALLBACK = frozenset((128, 256, 512, 1024, 2048))

    _RX_STORAGE_POSICIONAL = re.compile(
        r"\b\d{1,3}\s*(?:gb)?\s*(?:de\s+)?(?:ram|memoria)\b\s+(\d{2,4})\b",
        re.IGNORECASE,
    )

    @classmethod
    def _numero_storage(cls, linea: str) -> int | None:
        directo = cls._storage_directo(linea)
        if directo is not None:
            return directo
        posicional = cls._storage_posicional(linea)
        if posicional is not None:
            return posicional
        # Desambiguacion simetrica: si hay "16GB 512GB", el mayor (>=128) es storage.
        m = cls._RX_DOS_GB.search(linea)
        if m:
            try:
                a, b = int(m.group(1)), int(m.group(2))
                menor, mayor = (a, b) if a <= b else (b, a)
                if menor in cls._RAM_VALIDOS and mayor in cls._SSD_VALIDOS_TOTAL:
                    return mayor
            except (ValueError, TypeError):
                pass
        return None

    @classmethod
    def _storage_directo(cls, linea: str) -> int | None:
        m = cls._STORAGE_RX.search(linea)
        if not m:
            return None
        # group(4) es el nuevo patron "512GB SSD" / "512GBSSD" (sin espacio).
        valor = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        try:
            v = int(valor)
        except (ValueError, TypeError):
            return None
        if m.group(3):
            v *= 1024
        return v if v in cls._SSD_VALIDOS_TOTAL else None

    @classmethod
    def _storage_posicional(cls, linea: str) -> int | None:
        """Fallback: '16 ram 512' — segundo numero canonico tras RAM."""
        m = cls._RX_STORAGE_POSICIONAL.search(linea)
        if not m:
            return None
        try:
            v = int(m.group(1))
        except (ValueError, TypeError):
            return None
        return v if v in cls._SSD_VALIDOS_FALLBACK else None

    @classmethod
    def _numero_precio(cls, linea: str) -> float | None:
        m = cls._PRECIO_RX.search(linea)
        if not m:
            return None
        valor = m.group(1) or m.group(2)
        try:
            return float(valor.replace(".", "").replace(",", ""))
        except (ValueError, TypeError):
            return None

    @classmethod
    def _numero_pulgadas(cls, linea: str) -> float | None:
        m = cls._PULGADAS_RX.search(linea)
        if not m:
            return None
        try:
            return float(m.group(1).replace(",", "."))
        except (ValueError, TypeError):
            return None
