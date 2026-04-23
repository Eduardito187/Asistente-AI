from __future__ import annotations

import re


class NormalizadorFormatoProducto:
    """SRP: asegura que cada línea de producto siga el formato canónico
    `Nombre — Bs precio [SKU]`. Implementa la regla 3 del prompt como
    post-processor determinista. Acepta las variantes más comunes del LLM
    (separadores `-`, `:`, `(...)`; símbolos `$`, `Bs.`, `BOB`) y las
    converge al formato único que la UI renderiza como tarjeta.
    """

    _RX_SKU = re.compile(r"\[([A-Z0-9][A-Z0-9\-./#()]{2,})\]")
    # Sólo reconocemos un número como precio cuando está adyacente a un
    # marcador de moneda (prefijo "Bs 1039", sufijo "1039 Bs / bolivianos").
    # Sin marcador, dejamos la línea tal cual — no inventamos precio sobre
    # números que podrían ser modelo/pulgadas/capacidad.
    _RX_PRECIO_PREFIJO = re.compile(
        r"(?:Bs\.?|BOB|\$|US\$|USD)\s*(?P<monto>\d+(?:[.,]\d{3})*(?:[.,]\d+)?)",
        re.IGNORECASE,
    )
    _RX_PRECIO_SUFIJO = re.compile(
        r"(?P<monto>\d+(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(?:Bs\.?|BOB|bolivianos)\b",
        re.IGNORECASE,
    )

    @classmethod
    def normalizar(cls, respuesta: str) -> str:
        if not respuesta:
            return respuesta
        lineas = respuesta.split("\n")
        salida: list[str] = []
        for linea in lineas:
            if cls._es_linea_de_producto(linea):
                salida.append(cls._normalizar_linea(linea))
            else:
                salida.append(linea)
        return "\n".join(salida)

    _RX_BULLET_INICIO = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")

    @classmethod
    def _es_linea_de_producto(cls, linea: str) -> bool:
        """Una 'línea de producto' es una entrada de lista (bullet `-`/`*`/
        numeración `1.`) que contiene un [SKU]. Texto en prosa con [SKU] no
        se toca — preservamos la frase del LLM."""
        if not cls._RX_BULLET_INICIO.match(linea):
            return False
        if not cls._RX_SKU.search(linea):
            return False
        return bool(re.search(r"\d{2,}", linea))

    @classmethod
    def _normalizar_linea(cls, linea: str) -> str:
        """Re-arma la línea como `<prefix>Nombre — Bs monto[ (antes Bs prev)] [SKU]<resto>`.
        Si algo no calza (sin precio identificable), devuelve la línea tal cual."""
        m_sku = cls._RX_SKU.search(linea)
        if not m_sku:
            return linea
        sku = m_sku.group(1)
        antes_sku = linea[: m_sku.start()].rstrip()
        despues_sku = linea[m_sku.end() :]
        bullet, cuerpo = cls._separar_bullet(antes_sku)
        monto, monto_anterior, nombre = cls._extraer_precio_y_nombre(cuerpo)
        if monto is None or not nombre:
            return linea
        precio_fmt = f"Bs {cls._formato_monto(monto)}"
        if monto_anterior is not None and monto_anterior > monto:
            precio_fmt += f" (antes Bs {cls._formato_monto(monto_anterior)})"
        return f"{bullet}{nombre} — {precio_fmt} [{sku}]{despues_sku}"

    @staticmethod
    def _separar_bullet(texto: str) -> tuple[str, str]:
        """Preserva el bullet inicial (`- `, `* `, `1. `, etc.) sin tocarlo."""
        m = re.match(r"^(\s*(?:[-*•]|\d+[.)])\s+)", texto)
        if not m:
            return "", texto
        return m.group(1), texto[m.end() :]

    @classmethod
    def _extraer_precio_y_nombre(
        cls, texto: str
    ) -> tuple[float | None, float | None, str]:
        """Extrae primer precio (actual) y, si existe, el anterior (mayor).
        Requiere marcador de moneda adyacente al número (Bs/BOB/$/bolivianos).
        Todo lo que quede al frente del primer precio es el nombre."""
        montos: list[tuple[int, int, float]] = []
        for rx in (cls._RX_PRECIO_PREFIJO, cls._RX_PRECIO_SUFIJO):
            for m in rx.finditer(texto):
                valor = cls._a_float(m.group("monto"))
                if valor is None or valor < 1:
                    continue
                montos.append((m.start(), m.end(), valor))
        if not montos:
            return None, None, texto.strip()
        montos.sort(key=lambda t: t[0])
        primero = montos[0]
        nombre = cls._limpiar_nombre(texto[: primero[0]])
        # Descartamos todo frecuencia mm/cm/pulgadas: para hitos de precio
        # anterior pedimos un segundo monto MAYOR al primero (descuento).
        actual = primero[2]
        anterior = next(
            (v for _, _, v in montos[1:] if v > actual),
            None,
        )
        return actual, anterior, nombre.strip()

    @staticmethod
    def _limpiar_nombre(texto: str) -> str:
        """Recorta separadores y stopwords que el LLM deja pegadas antes del
        precio ("Galaxy A06 por", "ThinkBook 16 a"). Stopwords conocidas: a,
        por, en, de — preposiciones que conectan nombre con precio y no
        aportan al nombre del producto."""
        limpio = texto.rstrip(" -—–:·;|()")
        limpio = re.sub(
            r"\s+(?:a|por|en|de)\s*$", "", limpio, flags=re.IGNORECASE
        )
        return limpio.strip()

    @staticmethod
    def _a_float(raw: str) -> float | None:
        """Acepta '1.039', '1,039', '1039' — normaliza el separador de miles."""
        txt = raw.strip()
        # Heuristica: si hay punto Y coma, el ultimo es decimal; el otro es miles.
        if "," in txt and "." in txt:
            if txt.rfind(",") > txt.rfind("."):
                txt = txt.replace(".", "").replace(",", ".")
            else:
                txt = txt.replace(",", "")
        elif "," in txt:
            # Si hay exactamente un grupo de 3 digitos despues de la coma, es miles.
            piezas = txt.split(",")
            if len(piezas) == 2 and len(piezas[1]) == 3:
                txt = piezas[0] + piezas[1]
            else:
                txt = txt.replace(",", ".")
        # Punto solo: si hay un grupo de 3 digitos despues, es miles.
        elif "." in txt:
            piezas = txt.split(".")
            if len(piezas) == 2 and len(piezas[1]) == 3:
                txt = piezas[0] + piezas[1]
        try:
            return float(txt)
        except ValueError:
            return None

    @staticmethod
    def _formato_monto(valor: float) -> str:
        """Formato boliviano: miles con punto, sin decimales."""
        entero = int(round(valor))
        return f"{entero:,}".replace(",", ".")
