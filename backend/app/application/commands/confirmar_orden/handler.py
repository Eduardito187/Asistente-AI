from __future__ import annotations

from typing import Callable

from ....domain.ordenes import DatosCliente, Orden, OrdenItem
from ....domain.shared.errors import ReglaDeNegocioViolada
from ...ports import UnitOfWork
from .command import ConfirmarOrdenCommand
from .result import ResultadoConfirmarOrden


class ConfirmarOrdenHandler:
    """Handler CQRS: valida carrito, crea orden, convierte sesion y vacia carrito."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: ConfirmarOrdenCommand) -> ResultadoConfirmarOrden:
        cliente = DatosCliente(
            nombre=cmd.cliente_nombre,
            email=(cmd.cliente_email or "").strip() or None,
            telefono=(cmd.cliente_telefono or "").strip() or None,
        )

        with self._uow_factory() as uow:
            sesion = uow.sesiones.obtener(cmd.sesion_id)
            if sesion is None:
                raise ReglaDeNegocioViolada("sesion inexistente")

            carrito = uow.carritos.obtener(cmd.sesion_id)
            if carrito.esta_vacio():
                raise ReglaDeNegocioViolada("el carrito esta vacio, no se puede confirmar")

            items_orden = [
                OrdenItem(
                    sku=item.sku,
                    nombre=item.nombre,
                    marca=None,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                )
                for item in carrito.items
            ]
            skus_a_marca = {
                str(p.sku): p.marca
                for p in uow.productos.obtener_varios([i.sku for i in items_orden])
            }
            for i in items_orden:
                i.marca = skus_a_marca.get(str(i.sku))

            orden = Orden.nueva(
                sesion_id=cmd.sesion_id,
                cliente=cliente,
                items=items_orden,
                notas=(cmd.notas or "").strip() or None,
            )
            orden_persistida = uow.ordenes.persistir(orden)

            uow.carritos.vaciar(cmd.sesion_id)
            sesion.marcar_convertida(cliente.nombre, cliente.email, cliente.telefono)
            uow.sesiones.guardar(sesion)

            uow.commit()

            return ResultadoConfirmarOrden(
                numero_orden=orden_persistida.numero_orden or "",
                orden_id=str(orden_persistida.id),
                total_bob=orden_persistida.total_bob,
                items_cantidad=orden_persistida.items_cantidad,
                cliente_nombre=cliente.nombre,
                cliente_email=cliente.email,
                cliente_telefono=cliente.telefono,
            )
