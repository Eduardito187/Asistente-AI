from __future__ import annotations

import re
from typing import Iterable, Optional


class VerificadorClaimsProducto:
    """SRP: valida claims numéricos cerca de cada [SKU] en la respuesta del
    agente contra los datos reales del producto. Cuando un claim difiere,
    reescribe el span con el valor correcto.

    Protege contra mentiras sutiles del LLM como 'Galaxy S26 Bs 12.000' cuando
    el catálogo lo tiene a Bs 18.699, o 'iPhone 17 Pro Max 512 GB' cuando es
    de 256 GB. No corrige lo que NO puede verificar (descripción narrativa).

    Algoritmo por SKU:
      1. Ubicar cada `[SKU]` en el texto → posición.
      2. Definir ventana: 140 chars antes + 40 después.
      3. Buscar patrones (precio, pulgadas, GB, RAM, color) en esa ventana.
      4. Comparar vs producto real en el catálogo.
      5. Reescribir solo spans incorrectos — no toca el resto del texto.
    """

    _RX_SKU = re.compile(r"\[([A-ZÑ0-9][A-ZÑ0-9\-.#_/()]{2,60})\]", re.IGNORECASE)
    _RX_PRECIO = re.compile(r"Bs\s*([\d.,]+)", re.IGNORECASE)
    _RX_PULGADAS = re.compile(r'(\d+(?:[.,]\d+)?)\s*(?:pulgadas?|")', re.IGNORECASE)
    _RX_RAM = re.compile(r"(\d+)\s*GB(?:\s+(?:de\s+)?RAM)", re.IGNORECASE)
    _RX_ALMACENAMIENTO_EXPLICITO = re.compile(
        r"(\d+)\s*GB(?:\s+(?:de\s+)?(?:almacenamiento|storage|interno|disco|memoria\s+interna))",
        re.IGNORECASE,
    )

    _VENTANA_ANTES = 140
    _VENTANA_DESPUES = 40
    _TOLERANCIA_PRECIO_PCT = 0.01  # ±1% por redondeo "Bs 18,700 vs 18,699"

    @classmethod
    def corregir(cls, respuesta: str, productos: Iterable[dict]) -> str:
        """Reescribe `respuesta` corrigiendo claims erróneos cerca de cada SKU.
        `productos` debe ser la lista de dicts con {sku, precio_bob, ...} del
        catálogo real (viene de `_sanear_skus_y_enriquecer`).
        """
        if not respuesta or not productos:
            return respuesta
        por_sku = {str(p.get("sku")): p for p in productos if p.get("sku")}
        # Recorrer SKUs de derecha a izquierda para que los offsets no se corran.
        matches = list(cls._RX_SKU.finditer(respuesta))
        for m in reversed(matches):
            prod = por_sku.get(m.group(1))
            if not prod:
                continue
            inicio = max(0, m.start() - cls._VENTANA_ANTES)
            fin = min(len(respuesta), m.end() + cls._VENTANA_DESPUES)
            respuesta = (
                respuesta[:inicio]
                + cls._corregir_ventana(respuesta[inicio:fin], prod)
                + respuesta[fin:]
            )
        return respuesta

    @classmethod
    def _corregir_ventana(cls, ventana: str, prod: dict) -> str:
        ventana = cls._corregir_precio(ventana, prod)
        ventana = cls._corregir_pulgadas(ventana, prod)
        ventana = cls._corregir_ram(ventana, prod)
        ventana = cls._corregir_almacenamiento(ventana, prod)
        return ventana

    # ----- correctores puntuales -----

    @classmethod
    def _corregir_precio(cls, texto: str, prod: dict) -> str:
        precio_real = cls._a_float(prod.get("precio_bob"))
        if precio_real is None:
            return texto
        def reemplazar(m: re.Match) -> str:
            dicho = cls._precio_texto_a_float(m.group(1))
            if dicho is None or cls._precio_ok(dicho, precio_real):
                return m.group(0)
            return f"Bs {int(precio_real)}"
        return cls._RX_PRECIO.sub(reemplazar, texto)

    @classmethod
    def _corregir_pulgadas(cls, texto: str, prod: dict) -> str:
        real = cls._a_float(prod.get("atributos", {}).get("pulgadas") if prod.get("atributos") else prod.get("pulgadas"))
        if real is None:
            return texto
        def reemplazar(m: re.Match) -> str:
            try:
                dicho = float(m.group(1).replace(",", "."))
            except ValueError:
                return m.group(0)
            if abs(dicho - real) <= 0.5:
                return m.group(0)
            sufijo_match = re.search(r'(pulgadas?|")', m.group(0), re.IGNORECASE)
            sufijo = sufijo_match.group(0) if sufijo_match else '"'
            return f"{real:g} {sufijo}"
        return cls._RX_PULGADAS.sub(reemplazar, texto)

    @classmethod
    def _corregir_ram(cls, texto: str, prod: dict) -> str:
        atributos = prod.get("atributos") or {}
        real = atributos.get("ram_gb") if isinstance(atributos, dict) else None
        if real is None:
            return texto
        def reemplazar(m: re.Match) -> str:
            try:
                dicho = int(m.group(1))
            except ValueError:
                return m.group(0)
            if dicho == real:
                return m.group(0)
            return re.sub(r"^\d+", str(real), m.group(0))
        return cls._RX_RAM.sub(reemplazar, texto)

    @classmethod
    def _corregir_almacenamiento(cls, texto: str, prod: dict) -> str:
        atributos = prod.get("atributos") or {}
        real = atributos.get("capacidad_gb") if isinstance(atributos, dict) else None
        if real is None:
            return texto
        def reemplazar(m: re.Match) -> str:
            try:
                dicho = int(m.group(1))
            except ValueError:
                return m.group(0)
            if dicho == real:
                return m.group(0)
            return re.sub(r"^\d+", str(real), m.group(0))
        return cls._RX_ALMACENAMIENTO_EXPLICITO.sub(reemplazar, texto)

    # ----- helpers -----

    @staticmethod
    def _a_float(v) -> Optional[float]:
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _precio_texto_a_float(s: str) -> Optional[float]:
        limpio = s.replace(".", "").replace(",", "")
        try:
            return float(limpio)
        except ValueError:
            return None

    @classmethod
    def _precio_ok(cls, dicho: float, real: float) -> bool:
        if real == 0:
            return dicho == 0
        return abs(dicho - real) / real <= cls._TOLERANCIA_PRECIO_PCT
