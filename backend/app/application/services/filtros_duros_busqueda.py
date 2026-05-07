from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FiltrosDurosBusqueda:
    """VO con todos los filtros NO-relajables que se aplican a una busqueda
    de alternativas. Existen para evitar parameter-count blowup en
    ManejadorProductoAusente y SugeridorProductosAlternativos.

    "Duros" significa: no se relajan en el fallback. Si el cliente exigio
    16GB de RAM o GPU dedicada, eso es un requisito obligatorio — el
    fallback puede relajar marca/categoria, pero NO estos."""

    precio_max: float | None = None
    precio_min: float | None = None
    nombre_excluye: tuple[str, ...] | None = None
    tipo_producto_excluye: tuple[str, ...] | None = None
    marca_excluye: tuple[str, ...] | None = None
    pulgadas: float | None = None
    ram_gb_min: int | None = None
    capacidad_gb_min: int | None = None
    gpu_dedicada: bool | None = None

    def como_kwargs(self) -> dict:
        """Aplana a dict, saltando los None/vacios — listo para pasar a
        BuscarProductosQuery."""
        return {
            k: v
            for k, v in (
                ("precio_max", self.precio_max),
                ("precio_min", self.precio_min),
                ("nombre_excluye", self.nombre_excluye),
                ("tipo_producto_excluye", self.tipo_producto_excluye),
                ("marca_excluye", self.marca_excluye),
                ("pulgadas", self.pulgadas),
                ("ram_gb_min", self.ram_gb_min),
                ("capacidad_gb_min", self.capacidad_gb_min),
                ("gpu_dedicada", self.gpu_dedicada),
            )
            if v not in (None, (), "", [])
        }
