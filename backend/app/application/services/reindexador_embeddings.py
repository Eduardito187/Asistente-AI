from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from ...domain.productos import SKU
from ...domain.productos_embeddings import ProductoEmbedding
from ..ports import EmbedderPort, UnitOfWork
from .codificador_vectorial import CodificadorVectorial

log = logging.getLogger("reindexador_embeddings")

BATCH = 32


class ReindexadorEmbeddings:
    """SRP: calcular y persistir los embeddings faltantes en lote."""

    def __init__(self, embedder: EmbedderPort, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._embedder = embedder
        self._uow_factory = uow_factory

    def reindexar_faltantes(self) -> int:
        modelo = self._embedder.modelo
        with self._uow_factory() as uow:
            pendientes = uow.productos_embeddings.skus_sin_embedding(modelo)
        total = 0
        for i in range(0, len(pendientes), BATCH):
            chunk = pendientes[i : i + BATCH]
            total += self._procesar_chunk(chunk, modelo)
        return total

    def _procesar_chunk(self, skus: list[str], modelo: str) -> int:
        with self._uow_factory() as uow:
            productos = uow.productos.obtener_varios([SKU(s) for s in skus])
            textos = [self._texto_de(p) for p in productos]
            vectores = self._embedder.embed(textos)
            if len(vectores) != len(productos):
                log.warning(
                    "embedder devolvio %s vectores para %s productos — abortando chunk",
                    len(vectores),
                    len(productos),
                )
                return 0
            ahora = datetime.utcnow()
            for producto, vec in zip(productos, vectores):
                uow.productos_embeddings.upsert(
                    ProductoEmbedding(
                        sku=str(producto.sku),
                        modelo=modelo,
                        vector=CodificadorVectorial.a_bytes(vec),
                        updated_at=ahora,
                    )
                )
            uow.commit()
        return len(productos)

    @staticmethod
    def _texto_de(p) -> str:
        partes = [p.nombre]
        if p.marca:
            partes.append(p.marca)
        if p.categoria:
            partes.append(p.categoria)
        if p.subcategoria:
            partes.append(p.subcategoria)
        if p.descripcion:
            partes.append(p.descripcion)
        return " | ".join(partes)
