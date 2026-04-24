from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import Engine, text

from ...application.ports import ProductoRepository
from ...domain.productos import ProductoRaw
from ...domain.sinonimos import ExpansorSinonimos
from ...domain.texto import NormalizadorTexto
from .sql import CatalogoAtributosSql, ProductoSql


def _bool_a_tinyint(valor: bool | None) -> int | None:
    """Convierte Optional[bool] al TINYINT(1) de MariaDB (NULL-safe)."""
    if valor is None:
        return None
    return 1 if valor else 0


class MariaDbProductoRepositorio(ProductoRepository):
    """Implementación MariaDB del repo de productos (upsert por SKU)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, producto: ProductoRaw, origen: str) -> None:
        _nombre_base = NormalizadorTexto.sin_acentos((producto.nombre or "").lower())
        nombre_norm = ExpansorSinonimos.expandir(_nombre_base)
        descripcion_norm = NormalizadorTexto.sin_acentos((producto.descripcion or "").lower()) or None
        marca_norm = NormalizadorTexto.sin_acentos((producto.marca or "").lower()) or None
        categoria_norm = NormalizadorTexto.sin_acentos((producto.categoria or "").lower()) or None
        atr = producto.atributos
        atributos_json = json.dumps(producto.atributos_json, ensure_ascii=False) if producto.atributos_json else None
        atributos_texto = self._construir_atributos_texto(producto.atributos_json) if producto.atributos_json else None

        with self._engine.begin() as conn:
            conn.execute(
                text(ProductoSql.UPSERT),
                {
                    "sku": producto.sku,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "categoria": producto.categoria,
                    "subcategoria": producto.subcategoria,
                    "marca": producto.marca,
                    "precio_bob": producto.precio_bob,
                    "precio_anterior_bob": producto.precio_anterior_bob,
                    "stock": producto.stock,
                    "imagen_url": producto.imagen_url,
                    "url_producto": producto.url_producto,
                    "activo": 1 if producto.activo else 0,
                    "origen": origen,
                    "nombre_norm": nombre_norm,
                    "descripcion_norm": descripcion_norm,
                    "marca_norm": marca_norm,
                    "categoria_norm": categoria_norm,
                    "pulgadas": atr.pulgadas,
                    "capacidad_gb": atr.capacidad_gb,
                    "ram_gb": atr.ram_gb,
                    "capacidad_litros": atr.capacidad_litros,
                    "capacidad_kg": atr.capacidad_kg,
                    "potencia_w": atr.potencia_w,
                    "procesador": atr.procesador,
                    "color": atr.color,
                    "tipo_panel": atr.tipo_panel,
                    "resolucion": atr.resolucion,
                    "bateria_mah": atr.bateria_mah,
                    "camara_mp": atr.camara_mp,
                    "camara_frontal_mp": atr.camara_frontal_mp,
                    "soporta_5g": _bool_a_tinyint(atr.soporta_5g),
                    "sistema_operativo": atr.sistema_operativo,
                    "refresh_hz": atr.refresh_hz,
                    "gpu": atr.gpu,
                    "tipo_producto": producto.tipo_producto,
                    "es_vestible": _bool_a_tinyint(producto.es_vestible),
                    "modelo": producto.modelo,
                    "meses_garantia": producto.meses_garantia,
                    "descripcion_extendida": producto.descripcion_extendida,
                    "caracteristicas": producto.caracteristicas,
                    "atributos": atributos_json,
                    "atributos_texto": atributos_texto,
                    "es_descontinuado": 1 if producto.es_descontinuado else 0,
                },
            )
            self._registrar_catalogo_atributos(conn, producto)

    @staticmethod
    def _construir_atributos_texto(atributos_json: dict) -> str:
        norm = NormalizadorTexto.sin_acentos
        partes: list[str] = []
        for col, valor in atributos_json.items():
            partes.append(norm(col.lower()))
            partes.append(norm(str(valor).lower()))
        return " ".join(partes)

    @staticmethod
    def _registrar_catalogo_atributos(conn, producto: ProductoRaw) -> None:
        if not producto.atributos_json:
            return
        categoria = producto.categoria or ""
        subcategoria = producto.subcategoria or ""
        for nombre in producto.atributos_json:
            conn.execute(
                text(CatalogoAtributosSql.UPSERT),
                {"categoria": categoria, "subcategoria": subcategoria, "nombre": nombre},
            )

    def insertar_catalogo(self, producto: ProductoRaw, origen: str) -> bool:
        """INSERT IGNORE: inserta solo si el SKU no existe. Retorna True si fue insertado."""
        _nombre_base = NormalizadorTexto.sin_acentos((producto.nombre or "").lower())
        nombre_norm = ExpansorSinonimos.expandir(_nombre_base)
        marca_norm = NormalizadorTexto.sin_acentos((producto.marca or "").lower()) or None
        categoria_norm = NormalizadorTexto.sin_acentos((producto.categoria or "").lower()) or None
        atr = producto.atributos
        atributos_json = json.dumps(producto.atributos_json, ensure_ascii=False) if producto.atributos_json else None
        atributos_texto = self._construir_atributos_texto(producto.atributos_json) if producto.atributos_json else None

        with self._engine.begin() as conn:
            res = conn.execute(
                text(ProductoSql.INSERT_CATALOGO),
                {
                    "sku": producto.sku,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "categoria": producto.categoria,
                    "subcategoria": producto.subcategoria,
                    "marca": producto.marca,
                    "origen": origen,
                    "nombre_norm": nombre_norm,
                    "marca_norm": marca_norm,
                    "categoria_norm": categoria_norm,
                    "pulgadas": atr.pulgadas,
                    "capacidad_gb": atr.capacidad_gb,
                    "ram_gb": atr.ram_gb,
                    "capacidad_litros": atr.capacidad_litros,
                    "capacidad_kg": atr.capacidad_kg,
                    "potencia_w": atr.potencia_w,
                    "procesador": atr.procesador,
                    "color": atr.color,
                    "tipo_panel": atr.tipo_panel,
                    "resolucion": atr.resolucion,
                    "bateria_mah": atr.bateria_mah,
                    "camara_mp": atr.camara_mp,
                    "camara_frontal_mp": atr.camara_frontal_mp,
                    "soporta_5g": _bool_a_tinyint(atr.soporta_5g),
                    "sistema_operativo": atr.sistema_operativo,
                    "refresh_hz": atr.refresh_hz,
                    "gpu": atr.gpu,
                    "tipo_producto": producto.tipo_producto,
                    "es_vestible": _bool_a_tinyint(producto.es_vestible),
                    "modelo": producto.modelo,
                    "meses_garantia": producto.meses_garantia,
                    "descripcion_extendida": producto.descripcion_extendida,
                    "caracteristicas": producto.caracteristicas,
                    "atributos": atributos_json,
                    "atributos_texto": atributos_texto,
                    "es_descontinuado": 1 if producto.es_descontinuado else 0,
                },
            )
            insertado = int(res.rowcount or 0) > 0
            if insertado:
                self._registrar_catalogo_atributos(conn, producto)
            return insertado

    def desactivar_faltantes(self, origen: str, skus_vistos: Iterable[str]) -> int:
        vistos = list(skus_vistos)
        if not vistos:
            return 0
        params: dict = {f"s{i}": s for i, s in enumerate(vistos)}
        params["o"] = origen
        with self._engine.begin() as conn:
            res = conn.execute(text(ProductoSql.desactivar_faltantes(len(vistos))), params)
            return int(res.rowcount or 0)
