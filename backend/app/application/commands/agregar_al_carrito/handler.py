from __future__ import annotations

from typing import Callable

from ....domain.productos import SKU
from ....domain.shared.errors import EntidadNoEncontrada, ReglaDeNegocioViolada
from ...ports import UnitOfWork
from .command import AgregarAlCarritoCommand
from .result import ResultadoAgregar


class AgregarAlCarritoHandler:
    """Handler CQRS: valida stock, persiste item y toca la sesion."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: AgregarAlCarritoCommand) -> ResultadoAgregar:
        cantidad = max(1, int(cmd.cantidad or 1))
        sku = SKU(cmd.sku)
        with self._uow_factory() as uow:
            producto = uow.productos.obtener_por_sku(sku)
            if producto is None or not producto.activo:
                raise EntidadNoEncontrada(f"SKU {sku} no existe")
            if producto.stock <= 0:
                raise ReglaDeNegocioViolada(f"{sku} sin stock")

            uow.sesiones.tocar(cmd.sesion_id)
            uow.carritos.agregar_o_incrementar(cmd.sesion_id, sku, cantidad)
            uow.commit()

            return ResultadoAgregar(
                sku=str(sku),
                nombre=producto.nombre,
                cantidad_agregada=cantidad,
                precio_unitario_bob=producto.precio.monto,
            )
