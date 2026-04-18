from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import ProductoInvalido


@dataclass(frozen=True)
class ProductoRaw:
    """VO inmutable que representa un producto tal como llega desde un origen externo.

    Las invariantes son minimas a proposito: sku y nombre no vacios, precio > 0.
    Todo lo demas es responsabilidad del adaptador o del clasificador.
    """

    sku: str
    nombre: str
    descripcion: Optional[str]
    categoria: Optional[str]
    subcategoria: Optional[str]
    marca: Optional[str]
    precio_bob: float
    precio_anterior_bob: Optional[float]
    stock: int
    imagen_url: Optional[str]
    url_producto: Optional[str]
    activo: bool = True

    def __post_init__(self) -> None:
        if not (self.sku or "").strip():
            raise ProductoInvalido("sku vacio")
        if not (self.nombre or "").strip():
            raise ProductoInvalido("nombre vacio")
        if self.precio_bob is None or self.precio_bob <= 0:
            raise ProductoInvalido(f"precio invalido: {self.precio_bob}")
        if self.stock < 0:
            raise ProductoInvalido(f"stock negativo: {self.stock}")
