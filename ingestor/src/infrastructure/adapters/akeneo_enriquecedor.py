"""Enriquece ProductoRaw con atributos estructurados del PIM Akeneo.

Carga el CSV procesado una sola vez en memoria (dict SKU → datos).
Columnas duplicadas: se conserva el primer valor no vacío.
Valores centinela 'N' (Akeneo null) se tratan como vacío.
"""
from __future__ import annotations

import csv
import json
import logging
from typing import Iterable, Optional

from ...domain.clasificacion import Clasificador
from ...domain.productos import ProductoRaw
from ...domain.texto import NormalizadorTexto

log = logging.getLogger("ingestor.akeneo_enriquecedor")

csv.field_size_limit(10_000_000)

_COL_DESCRIPCION: str = "Descripción"
_COL_MESES_GARANTIA: str = "Meses Garantía"

# ── columnas de identidad / operacionales ─────────────────────────────────────
# Estas NO se meten en atributos_json — son SKU, categorización o datos internos.
_COLS_EXCLUIR_JSON: frozenset[str] = frozenset({
    "Código", "categories", "enabled", "family",
    "Clacom", "Cod. Categoria", "Cod. Conjunto", "Cod. Subcategoria",
    "Articulo de compra", "Articulo de inventario", "Articulo de venta",
    "Articulo gestionado por", "Cantidad de pedido mínima", "Pedido multiple",
    "Intervalo de pedido", "Metodo de aprovisionamiento",
    "Metodo de contabilizacion", "Metodo de gestion", "Metodo de planificacion",
    "Sujeto a impuestos", "Sujeto a retencion de impuestos",
    "Aplica Factor Contado", "Aplica Factor Minicuota",
    "Plazo extendido minicuotas", "Gestión Stock por almacén",
    "Unification Stock", "Fijar cuentas de mayor", "Fast Cloud Tipo Trabajo",
    "Proveedor determinado", "Nandina", "Codigo Anterior", "Codigo barra",
    "Código de barra", "Actividad Económica", "Actividad Económica Mayorista",
    "Producto SIN - GSE_ProductoSIN-es_BO",
    "Producto SIN - GSE_ProductoSIN_Mayorista-es_BO",
    "Descuento_preorden", "Duracion_preorden", "Pre Orden",
    "Despacho", "Despacho Express", "Entrega Automática", "Forma de entrega",
    "Días de tolerancia", "Estado (activo o inactivo)",
    "Politica de Garantía y mantenimiento", "Speach Comercial",
    "Ficha técnica", "Category Responsable", "Ubicación",
    "Tiempo de atención", "Lead time proveedor (dropship)", "Activar Dropship",
    "Maestro LongTail", "Requiere numero de serie", "IMEI",
    "Categoria", "Categoria ecommerce", "Subcategoria",
    "Modelo", _COL_MESES_GARANTIA, _COL_DESCRIPCION, "Marca",
    "Característica 1", "Característica 2", "Característica 3",
    "Característica 4", "Característica 5", "Características unicas",
    "Tipo de producto - Tipo_de_producto-es_BO",
    "Tipo de producto - Tipo_de_prodcuto-es_BO",
    "Tipo de producto.",
    "created", "updated",
    # Datos de garantía (direcciones y teléfonos) — no son atributos de producto
    "Dirección - Cochabamba - Garantia_dismac_direccion_cbba",
    "Dirección - La Paz - Garantia_dismac_direccion_lpz",
    "Dirección - Santa Cruz - Garantia_dismac_direccion_scz",
    "Dirección - Sucre - Garantia_dismac_direccion_sucre",
    "Dirección - Tarija",
    "Teléfono - Cochabamba", "Teléfono - La Paz",
    "Teléfono - Santa Cruz - Garantia_dismac_telefono_scz-es_BO",
    "Telefono - Sucre", "Telefono - Tarija",
    "Dirección - Cochabamba - Garantia_externa_direccion_cbba",
    "Dirección - La Paz - Garantia_externa_direccion_lpz",
    "Dirección - Santa Cruz - Garantia_externa_direccion_scz",
    "Dirección - Sucre - Garantia_externa_direccion_sucre",
    "Nombre o Contacto - Cochabamba", "Nombre o Contacto - La Paz",
    "Nombre o Contacto - Santa Cruz", "Nombre o Contacto Sucre",
    "Nombre o Contacto - Tarija",
})

# ── familias que implican es_vestible = True ───────────────────────────────────
_FAMILIES_VESTIBLE: frozenset[str] = frozenset({
    "relojes de pulsera",
    "smartwatch",
    "smartwatches",
    "pulseras inteligentes",
    "wearables",
})
_TIPO_VESTIBLE_KEYWORDS: tuple[str, ...] = (
    "pulsera", "smartwatch", "reloj inteligente", "banda inteligente", "wearable",
)

# ── patrones de columnas operacionales (sin importar variantes de acento) ─────
# Columna se excluye si su nombre CONTIENE alguno de estos fragmentos (lower).
_PATRONES_EXCLUIR_JSON: tuple[str, ...] = (
    "dirección", "direccion",
    "teléfono", "telefono",
    "- tarija", "- cochabamba", "- la paz", "- santa cruz", "- sucre",
    "garantia_dismac", "garantia_externa",
    "-es_bo",           # variantes de locale akeneo
    "mayorista",
)

# ── columnas de pantalla (hay dos variantes de nombre) ────────────────────────
_COLS_PULGADAS: tuple[str, ...] = (
    "Tamaño de pantalla - Tamano_de_pantalla-es_BO",
    "Tamaño de pantalla - Tama_o_de_pantalla-es_BO",
    "Tamaño de pantalla Smart Wach",
)

# ── columnas de tipo_producto (tres variantes) ────────────────────────────────
_COLS_TIPO_PRODUCTO: tuple[str, ...] = (
    "Tipo de producto - Tipo_de_producto-es_BO",
    "Tipo de producto - Tipo_de_prodcuto-es_BO",
    "Tipo de producto.",
)


class AkeneoEnriquecedor:
    """Carga el CSV de Akeneo en memoria y enriquece ProductoRaw por SKU.

    Responsabilidad única: dado un ProductoRaw, devuelve una copia con los
    campos Akeneo rellenos (tipo_producto, modelo, meses_garantia, etc.).
    Si el SKU no existe en el PIM devuelve el raw sin modificar."""

    def __init__(self, path: str) -> None:
        self._datos: dict[str, dict] = {}
        self._headers: list[str] = []
        self._cargar(path)

    def enriquecer(self, raw: ProductoRaw) -> ProductoRaw:
        fila = self._datos.get(raw.sku.strip())
        if not fila:
            return raw
        tipo_producto = self._extraer_tipo_producto(fila)
        es_vestible = self._derivar_es_vestible(fila, tipo_producto)
        atributos_json = self._construir_atributos_json(fila)
        caracteristicas = self._extraer_caracteristicas(fila)
        desc_extendida = self._v(fila, _COL_DESCRIPCION) or None

        # AtributosProducto: Akeneo gana sobre regex cuando tiene valor
        atr = self._enriquecer_atributos(raw.atributos, fila)

        es_descontinuado = self._v(fila, "Clacom") == "Cat. X - Descontinuado"
        return ProductoRaw(
            sku=raw.sku,
            nombre=raw.nombre,
            descripcion=raw.descripcion or desc_extendida,
            categoria=raw.categoria,
            subcategoria=raw.subcategoria,
            marca=raw.marca or self._v(fila, "Marca") or None,
            precio_bob=raw.precio_bob,
            precio_anterior_bob=raw.precio_anterior_bob,
            stock=raw.stock,
            imagen_url=raw.imagen_url,
            url_producto=raw.url_producto,
            activo=raw.activo,
            atributos=atr,
            tipo_producto=tipo_producto,
            es_vestible=es_vestible,
            modelo=self._v(fila, "Modelo") or None,
            meses_garantia=self._int_v(fila, _COL_MESES_GARANTIA),
            descripcion_extendida=desc_extendida,
            caracteristicas=caracteristicas,
            atributos_json=atributos_json if atributos_json else None,
            es_descontinuado=es_descontinuado,
        )

    # ── catálogo completo ─────────────────────────────────────────────────────

    def iterar_catalogo(self, clasificador: Clasificador) -> Iterable[ProductoRaw]:
        """Genera ProductoRaw para TODOS los productos Akeneo (activo=False, sin precio).

        Solo omite productos sin ningún campo identificador útil (sin marca,
        modelo ni familia). El SKU siempre está presente.
        Úsese para poblar el catálogo completo más allá del feed web.
        """
        from ...domain.atributos import AtributosProducto
        for sku, fila in self._datos.items():
            nombre = self._construir_nombre_catalogo(sku, fila)
            if not nombre:
                continue
            marca = self._v(fila, "Marca") or None
            tipo_producto = self._extraer_tipo_producto(fila)
            es_vestible = self._derivar_es_vestible(fila, tipo_producto)
            es_descontinuado = self._v(fila, "Clacom") == "Cat. X - Descontinuado"
            atributos_json = self._construir_atributos_json(fila)
            caracteristicas = self._extraer_caracteristicas(fila)
            desc = self._v(fila, _COL_DESCRIPCION) or None
            atr_base = AtributosProducto()
            atr = self._enriquecer_atributos(atr_base, fila)
            categoria, subcategoria = clasificador.clasificar(nombre, marca=marca)
            try:
                yield ProductoRaw(
                    sku=sku,
                    nombre=nombre,
                    descripcion=desc,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    marca=marca,
                    precio_bob=0.0,
                    precio_anterior_bob=None,
                    stock=0,
                    imagen_url=None,
                    url_producto=None,
                    activo=False,
                    atributos=atr,
                    tipo_producto=tipo_producto,
                    es_vestible=es_vestible,
                    modelo=self._v(fila, "Modelo") or None,
                    meses_garantia=self._int_v(fila, _COL_MESES_GARANTIA),
                    descripcion_extendida=desc,
                    caracteristicas=caracteristicas,
                    atributos_json=atributos_json if atributos_json else None,
                    es_descontinuado=es_descontinuado,
                )
            except Exception:
                continue

    @staticmethod
    def _construir_nombre_catalogo(sku: str, fila: dict) -> str:
        """Construye el mejor nombre posible desde datos Akeneo (sin nombre de producto)."""
        marca = fila.get("Marca", "").strip()
        if marca.upper() == "N":
            marca = ""
        modelo = fila.get("Modelo", "").strip()
        if modelo.upper() == "N":
            modelo = ""
        familia = fila.get("family", "").strip()

        if marca and modelo:
            return f"{marca} {modelo}"[:500]
        if marca and familia:
            return f"{familia} {marca}"[:500]
        if familia:
            return f"{familia} {sku}"[:500]
        return ""

    # ── carga ─────────────────────────────────────────────────────────────────

    def _cargar(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.reader(f, delimiter=";")
                self._headers = next(reader)
                for row in reader:
                    datos = self._row_a_dict(row)
                    sku = datos.get("Código", "").strip()
                    if sku:
                        self._datos[sku] = datos
            log.info("Akeneo: %d productos cargados desde %s", len(self._datos), path)
        except FileNotFoundError:
            log.warning("Akeneo CSV no encontrado en %s — enriquecimiento desactivado", path)
        except Exception as exc:
            log.error("Error cargando Akeneo CSV: %s", exc)

    def _row_a_dict(self, row: list[str]) -> dict[str, str]:
        """Convierte fila a dict. Para columnas duplicadas conserva el primer valor no vacío."""
        out: dict[str, str] = {}
        for header, value in zip(self._headers, row):
            v = value.strip()
            if v.upper() == "N":
                v = ""
            if header not in out or (not out[header] and v):
                out[header] = v
        return out

    # ── extracción de campos fijos ────────────────────────────────────────────

    def _extraer_tipo_producto(self, fila: dict) -> Optional[str]:
        for col in _COLS_TIPO_PRODUCTO:
            v = fila.get(col, "").strip()
            if v:
                return v.lower()
        return None

    @staticmethod
    def _derivar_es_vestible(fila: dict, tipo_producto: Optional[str]) -> Optional[bool]:
        family = fila.get("family", "").strip().lower()
        if family in _FAMILIES_VESTIBLE:
            return True
        if tipo_producto and any(kw in tipo_producto for kw in _TIPO_VESTIBLE_KEYWORDS):
            return True
        return None

    def _extraer_caracteristicas(self, fila: dict) -> Optional[str]:
        partes = []
        unicas = self._v(fila, "Características unicas")
        if unicas:
            partes.append(unicas)
        for i in range(1, 6):
            v = self._v(fila, f"Característica {i}")
            if v:
                partes.append(v)
        return "\n".join(partes) if partes else None

    def _construir_atributos_json(self, fila: dict) -> dict:
        """Devuelve dict con atributos dinámicos (no fijos). Excluye vacíos y operacionales."""
        resultado: dict[str, str] = {}
        for col, valor in fila.items():
            if col in _COLS_EXCLUIR_JSON:
                continue
            if col.endswith("(unit)"):
                continue
            col_lower = col.lower()
            if any(p in col_lower for p in _PATRONES_EXCLUIR_JSON):
                continue
            if not valor:
                continue
            resultado[col] = valor
        return resultado

    @staticmethod
    def _construir_atributos_texto(atributos: dict) -> str:
        """Texto plano de los atributos dinámicos para FULLTEXT."""
        norm = NormalizadorTexto.sin_acentos
        partes: list[str] = []
        for col, valor in atributos.items():
            partes.append(norm(col.lower()))
            partes.append(norm(valor.lower()))
        return " ".join(partes)

    # ── enriquecimiento de AtributosProducto ──────────────────────────────────

    def _enriquecer_atributos(self, atr, fila: dict):
        """Reemplaza campos de AtributosProducto solo cuando Akeneo tiene un valor mejor."""
        from ...domain.atributos import AtributosProducto
        return AtributosProducto(
            **self._specs_capacidad(atr, fila),
            **self._specs_display(atr, fila),
            **self._specs_camara(atr, fila),
            soporta_5g=atr.soporta_5g,
            sistema_operativo=(self._v(fila, "Sistema operativo")
                               or self._v(fila, "Sistema Operativo TV")
                               or atr.sistema_operativo),
            refresh_hz=atr.refresh_hz,
            gpu=atr.gpu,
        )

    def _specs_capacidad(self, atr, fila: dict) -> dict:
        return {
            "pulgadas": self._float_cols(fila, _COLS_PULGADAS) or atr.pulgadas,
            "capacidad_gb": (self._int_v(fila, "Capacidad de almacenamiento (Ecommerce)")
                             or self._int_v(fila, "Almacenamiento de Memoria (español Bolivia, Ecommerce)")
                             or atr.capacidad_gb),
            "ram_gb": self._int_v(fila, "Memoria RAM") or atr.ram_gb,
            "capacidad_litros": self._float_v(fila, "Capacidad (Lts)") or atr.capacidad_litros,
            "capacidad_kg": atr.capacidad_kg,
            "potencia_w": self._int_v(fila, "Potencia (Watts)") or atr.potencia_w,
            "procesador": self._norm_procesador(fila) or atr.procesador,
        }

    def _specs_display(self, atr, fila: dict) -> dict:
        return {
            "color": self._norm_color(fila) or atr.color,
            "tipo_panel": self._norm_tipo_panel(fila) or atr.tipo_panel,
            "resolucion": self._norm_resolucion(fila) or atr.resolucion,
            "bateria_mah": self._int_v(fila, "Capacidad de batería") or atr.bateria_mah,
        }

    def _specs_camara(self, atr, fila: dict) -> dict:
        return {
            "camara_mp": self._int_v(fila, "Camara Principal MP") or atr.camara_mp,
            "camara_frontal_mp": self._int_v(fila, "Camara Frontal MP") or atr.camara_frontal_mp,
        }

    def _norm_resolucion(self, fila: dict) -> Optional[str]:
        from ...domain.atributos import ExtractorAtributos
        raw = (self._v(fila, "Resolucion")
               or self._v(fila, "Resolución de Pantalla")
               or self._v(fila, "Tamaño de pantalla - Tamano_de_pantalla-es_BO"))
        return ExtractorAtributos.resolucion(raw) if raw else None

    def _norm_tipo_panel(self, fila: dict) -> Optional[str]:
        from ...domain.atributos import ExtractorAtributos
        raw = (self._v(fila, "Tecnología de Pantalla")
               or self._v(fila, "Tecnologia de Pantalla TV"))
        return ExtractorAtributos.tipo_panel(raw) if raw else None

    def _norm_procesador(self, fila: dict) -> Optional[str]:
        from ...domain.atributos import ExtractorAtributos
        raw = (self._v(fila, "Procesador Computadoras")
               or self._v(fila, "Procesador Celulares")
               or self._v(fila, "Procesador"))
        if not raw:
            return None
        return ExtractorAtributos.procesador(raw) or raw[:50]

    def _norm_color(self, fila: dict) -> Optional[str]:
        from ...domain.atributos import ExtractorAtributos
        raw = self._v(fila, "Color")
        return ExtractorAtributos.color(raw) if raw else None

    # ── helpers de lectura ────────────────────────────────────────────────────

    @staticmethod
    def _v(fila: dict, col: str) -> str:
        return fila.get(col, "").strip()

    def _int_v(self, fila: dict, col: str) -> Optional[int]:
        v = self._v(fila, col).split()[0] if self._v(fila, col) else ""
        try:
            return int(float(v.replace(",", "."))) if v else None
        except (ValueError, TypeError):
            return None

    def _float_v(self, fila: dict, col: str) -> Optional[float]:
        v = self._v(fila, col).split()[0] if self._v(fila, col) else ""
        try:
            return float(v.replace(",", ".")) if v else None
        except (ValueError, TypeError):
            return None

    def _float_cols(self, fila: dict, cols: tuple[str, ...]) -> Optional[float]:
        for col in cols:
            val = self._float_v(fila, col)
            if val is not None:
                return val
        return None
