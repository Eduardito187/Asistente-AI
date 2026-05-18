from __future__ import annotations

from typing import Callable

from sqlalchemy import text

from ...ports import UnitOfWork
from ...services.extractor_atributos_producto import ExtractorAtributosProducto
from ....infrastructure.persistence.mariadb.sql.cobertura_atributos_sql import CoberturaAtributosSql
from .query import CoberturaAtributosQuery
from .result import FilaCoberturaAtributos, ResultadoCoberturaAtributos

_CAMPOS = (
    "pulgadas", "ram_gb", "capacidad_gb", "refresh_hz", "bateria_mah",
    "camara_mp", "potencia_w", "capacidad_kg", "sistema_operativo",
    "tipo_panel", "resolucion", "soporta_5g", "gpu",
)


class CoberturaAtributosHandler:
    """Query handler: estadísticas de cobertura + batch enriquecimiento."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: CoberturaAtributosQuery) -> ResultadoCoberturaAtributos:
        with self._uow_factory() as uow:
            fila_global = uow._session.execute(text(CoberturaAtributosSql.COBERTURA)).mappings().one()
            global_ = self._construir_fila("(global)", fila_global)
            por_cat: list[FilaCoberturaAtributos] = []
            if q.por_categoria:
                filas = uow._session.execute(
                    text(CoberturaAtributosSql.COBERTURA_POR_CATEGORIA)
                ).mappings().all()
                por_cat = [self._construir_fila(f["categoria"] or "?", f) for f in filas]
        return ResultadoCoberturaAtributos(global_=global_, por_categoria=por_cat)

    def enriquecer_batch(self, limite: int = 500) -> dict:
        """Parsea productos con columnas vacías y persiste los valores extraídos."""
        actualizados = 0
        campos_total = 0
        with self._uow_factory() as uow:
            filas = uow._session.execute(
                text(CoberturaAtributosSql.PRODUCTOS_CON_COLUMNAS_VACIAS),
                {"limite": limite},
            ).mappings().all()
            for fila in filas:
                extraido = ExtractorAtributosProducto.extraer(
                    sku=fila["sku"],
                    nombre=fila["nombre"] or "",
                    descripcion=fila.get("descripcion"),
                    atributos_texto=fila.get("atributos_texto"),
                )
                if not extraido.campos_poblados:
                    continue
                params = {
                    "sku": extraido.sku,
                    "pulgadas": extraido.pulgadas,
                    "ram_gb": extraido.ram_gb,
                    "capacidad_gb": extraido.capacidad_gb,
                    "refresh_hz": extraido.refresh_hz,
                    "bateria_mah": extraido.bateria_mah,
                    "camara_mp": extraido.camara_mp,
                    "potencia_w": extraido.potencia_w,
                    "capacidad_kg": extraido.capacidad_kg,
                    "sistema_operativo": extraido.sistema_operativo,
                    "tipo_panel": extraido.tipo_panel,
                    "resolucion": extraido.resolucion,
                    "soporta_5g": 1 if extraido.soporta_5g else None,
                }
                uow._session.execute(text(CoberturaAtributosSql.ACTUALIZAR_ATRIBUTOS), params)
                actualizados += 1
                campos_total += len(extraido.campos_poblados)
            uow._session.commit()
        return {"productos_actualizados": actualizados, "campos_poblados": campos_total}

    @staticmethod
    def _construir_fila(categoria: str, fila) -> FilaCoberturaAtributos:
        total = int(fila["total"] or 0)
        atributos = {c: int(fila.get(c) or 0) for c in _CAMPOS}
        pcts = {
            c: round(atributos[c] / total * 100, 1) if total else 0.0
            for c in _CAMPOS
        }
        return FilaCoberturaAtributos(
            categoria=categoria,
            total=total,
            atributos=atributos,
            porcentajes=pcts,
        )
