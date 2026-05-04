"""Stubs minimos para tests sin DB ni FastAPI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakePrecio:
    monto: float


@dataclass
class FakeProducto:
    sku: str
    nombre: str
    procesador: Optional[str] = None
    ram_gb: Optional[int] = None
    capacidad_gb: Optional[int] = None
    gpu: Optional[str] = None
    precio: FakePrecio = field(default_factory=lambda: FakePrecio(0))
    marca: Optional[str] = None
    subcategoria: Optional[str] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    descripcion_extendida: Optional[str] = None
    caracteristicas: Optional[str] = None
    sistema_operativo: Optional[str] = None


@dataclass
class FakePerfil:
    ram_gb_min: Optional[int] = None
    ssd_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None
    presupuesto_max: Optional[float] = None
    presupuesto_ideal: Optional[float] = None
    uso_declarado: Optional[str] = None
    categoria_foco: Optional[str] = None
    desired_tier: Optional[str] = None
    pulgadas: Optional[float] = None
