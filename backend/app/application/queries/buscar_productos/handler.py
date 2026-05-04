from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields
from typing import Callable, Optional

from ....domain.productos import FiltrosAtributos, OpcionesBusqueda, Producto
from ....domain.shared.normalizacion import NormalizadorTexto
from ...ports import Cache, UnitOfWork
from .query import BuscarProductosQuery


class BuscarProductosHandler:
    """Handler CQRS: delega la busqueda al repo con textos normalizados.

    Cachea resultados por args normalizados con TTL corto — el catalogo
    cambia solo con el ingestor y mientras tanto la misma busqueda se
    repite mucho (saludo → "muestrame laptops" varias veces al dia).
    Si Redis no responde, el adaptador CacheNulo hace no-op transparente."""

    _TTL_CACHE_S = 60
    _CACHE_PREFIX = "buscar_productos:"

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        cache: Optional[Cache] = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._cache = cache

    def ejecutar(self, q: BuscarProductosQuery) -> list[Producto]:
        query_norm = NormalizadorTexto.normalizar(q.query)
        marca_norm = NormalizadorTexto.normalizar(q.marca) if q.marca else None
        cache_key = self._key(q, query_norm, marca_norm)
        cached_skus = self._cache_get(cache_key)
        if cached_skus is not None:
            return self._hidratar_por_sku(cached_skus)

        atributos = self._construir_filtros_atributos(q)
        opciones = self._construir_opciones(q)
        with self._uow_factory() as uow:
            productos = uow.productos.buscar(
                query_normalizada=query_norm,
                categoria=q.categoria or None,
                subcategoria=q.subcategoria or None,
                marca_normalizada=marca_norm,
                precio_min=q.precio_min,
                precio_max=q.precio_max,
                atributos=atributos,
                opciones=opciones,
                limite=max(1, min(q.limite, 20)),
            )
        self._cache_set(cache_key, [str(p.sku) for p in productos])
        return productos

    @staticmethod
    def _construir_opciones(q: BuscarProductosQuery) -> OpcionesBusqueda:
        return OpcionesBusqueda(
            solo_con_stock=q.solo_con_stock,
            solo_en_oferta=q.solo_en_oferta,
            excluir_accesorios=q.excluir_accesorios,
            solo_accesorios=q.solo_accesorios,
            orden_precio=q.orden_precio,
            excluir_skus=list(q.excluir_skus) if q.excluir_skus else None,
            genero=q.genero,
            nombre_excluye=list(q.nombre_excluye) if q.nombre_excluye else None,
        )

    @staticmethod
    def _construir_filtros_atributos(q: BuscarProductosQuery) -> FiltrosAtributos:
        """Construye el VO copiando todos los campos compartidos entre Query y
        FiltrosAtributos. Evita listar 60+ asignaciones a mano: cualquier campo
        que exista en ambos dataclasses se mapea automáticamente."""
        campos_atributos = {f.name for f in fields(FiltrosAtributos)}
        kwargs = {
            f.name: getattr(q, f.name)
            for f in fields(q)
            if f.name in campos_atributos
        }
        return FiltrosAtributos(**kwargs)

    def _hidratar_por_sku(self, skus: list[str]) -> list[Producto]:
        """Reconstruye los Producto desde los SKUs cacheados — evita
        serializar el agregado completo en Redis (descripciones grandes,
        atributos opcionales) y mantiene el dominio como source of truth."""
        if not skus:
            return []
        from ....domain.productos import SKU
        with self._uow_factory() as uow:
            return uow.productos.obtener_varios([SKU(s) for s in skus])

    @classmethod
    def _key(
        cls, q: BuscarProductosQuery, query_norm: str, marca_norm: Optional[str]
    ) -> str:
        payload = {
            **{k: v for k, v in asdict(q).items() if v is not None},
            "_qn": query_norm,
            "_mn": marca_norm,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return f"{cls._CACHE_PREFIX}{h}"

    def _cache_get(self, key: str) -> Optional[list[str]]:
        if self._cache is None:
            return None
        raw = self._cache.get(key)
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else None
        except (ValueError, TypeError):
            return None

    def _cache_set(self, key: str, skus: list[str]) -> None:
        if self._cache is None:
            return
        self._cache.set(key, json.dumps(skus), ttl_segundos=self._TTL_CACHE_S)
