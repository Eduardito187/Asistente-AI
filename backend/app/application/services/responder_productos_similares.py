from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...domain.productos import Producto, SKU
from ..ports import UnitOfWork
from .sugeridor_productos_alternativos import SugeridorProductosAlternativos


@dataclass(frozen=True)
class RespuestaSimilares:
    texto: str
    productos: list[Producto]
    sku_original: str


class ResponderProductosSimilares:
    """SRP: dado un SKU, busca alternativas reales con la misma categoria/
    subcategoria en un rango de precio cercano, excluyendo el SKU original.

    Short-circuit deterministico — no pasa por el LLM. El cliente ya esta
    viendo el producto original (vino del boton 'Similares' del card), asi
    que la respuesta se enfoca en las alternativas."""

    _LIMITE = 4
    _RANGO_PRECIO = 0.40  # +/- 40% del precio del original

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        sugeridor: SugeridorProductosAlternativos,
    ) -> None:
        self._uow_factory = uow_factory
        self._sugeridor = sugeridor

    def responder(self, sku: str) -> RespuestaSimilares | None:
        original = self._cargar_producto(sku)
        if original is None:
            return None
        alternativas = self._buscar_alternativas(original)
        if not alternativas:
            return RespuestaSimilares(
                texto=(
                    "No encontre alternativas cercanas en el catalogo para "
                    f"{original.nombre}. Contame que caracteristica queres "
                    "cambiar (precio, marca, tamanio) y busco opciones."
                ),
                productos=[],
                sku_original=sku,
            )
        return RespuestaSimilares(
            texto=self._formatear(original, alternativas),
            productos=alternativas,
            sku_original=sku,
        )

    def _cargar_producto(self, sku: str) -> Producto | None:
        with self._uow_factory() as uow:
            return uow.productos.obtener_por_sku(SKU(sku))

    def _buscar_alternativas(self, original: Producto) -> list[Producto]:
        precio = original.precio.monto
        precio_min = precio * (1 - self._RANGO_PRECIO)
        precio_max = precio * (1 + self._RANGO_PRECIO)
        resultados = self._sugeridor.sugerir(
            categoria=original.categoria,
            subcategoria=original.subcategoria,
            marca=None,
            nombre_canonico=None,
            precio_min=precio_min,
            precio_max=precio_max,
        )
        # El sugeridor no excluye SKUs por default — filtramos aqui el original.
        return [p for p in resultados if str(p.sku) != str(original.sku)][: self._LIMITE]

    @staticmethod
    def _formatear(original: Producto, alternativas: list[Producto]) -> str:
        cantidad = len(alternativas)
        plural = "opciones similares" if cantidad != 1 else "opcion similar"
        return (
            f"Aca tenes {cantidad} {plural} al {original.nombre} "
            f"en un rango de precio parecido. ¿Te interesa alguna?"
        )
