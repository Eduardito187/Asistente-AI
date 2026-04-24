from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .precio_bob import PrecioBob
from .sku import SKU


@dataclass(frozen=True)
class Producto:
    """Agregado de lectura del catálogo. El ingestor escribe, el backend lee."""

    sku: SKU
    nombre: str
    descripcion: Optional[str]
    categoria: Optional[str]
    subcategoria: Optional[str]
    marca: Optional[str]
    precio: PrecioBob
    precio_anterior: Optional[PrecioBob]
    stock: int
    imagen_url: Optional[str]
    activo: bool
    pulgadas: Optional[float] = None
    capacidad_gb: Optional[int] = None
    ram_gb: Optional[int] = None
    capacidad_litros: Optional[float] = None
    capacidad_kg: Optional[float] = None
    potencia_w: Optional[int] = None
    procesador: Optional[str] = None
    color: Optional[str] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    es_electrico: Optional[bool] = None
    bateria_mah: Optional[int] = None
    camara_mp: Optional[int] = None
    camara_frontal_mp: Optional[int] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    refresh_hz: Optional[int] = None
    gpu: Optional[str] = None
    tipo_producto: Optional[str] = None
    es_vestible: Optional[bool] = None
    modelo: Optional[str] = None
    meses_garantia: Optional[int] = None
    descripcion_extendida: Optional[str] = None
    caracteristicas: Optional[str] = None
    atributos: Optional[dict] = None
    es_descontinuado: bool = False

    def disponible(self) -> bool:
        return self.activo and self.stock > 0 and not self.es_descontinuado
