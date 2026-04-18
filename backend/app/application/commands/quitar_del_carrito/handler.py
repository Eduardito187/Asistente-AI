from __future__ import annotations

from typing import Callable

from ....domain.productos import SKU
from ....domain.shared.errors import EntidadNoEncontrada
from ...ports import UnitOfWork
from .command import QuitarDelCarritoCommand


class QuitarDelCarritoHandler:
    """Handler CQRS: quita un SKU del carrito, falla si no estaba."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: QuitarDelCarritoCommand) -> None:
        sku = SKU(cmd.sku)
        with self._uow_factory() as uow:
            uow.sesiones.tocar(cmd.sesion_id)
            quitado = uow.carritos.quitar(cmd.sesion_id, sku)
            if not quitado:
                raise EntidadNoEncontrada(f"{sku} no estaba en el carrito")
            uow.commit()
