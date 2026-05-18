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
    refresh_hz: Optional[int] = None
    bateria_mah: Optional[int] = None
    camara_mp: Optional[int] = None
    potencia_w: Optional[int] = None
    capacidad_kg: Optional[float] = None
    soporta_5g: Optional[bool] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    pulgadas: Optional[float] = None
    refresh_hz_min: Optional[int] = None
    bateria_mah_min: Optional[int] = None
    camara_mp_min: Optional[int] = None
    potencia_w_min: Optional[int] = None
    capacidad_kg_min: Optional[float] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    inverter: Optional[bool] = None
    no_frost: Optional[bool] = None
    smart_tv: Optional[bool] = None
    bluetooth_incluido: Optional[bool] = None
    nfc: Optional[bool] = None
    usb_c: Optional[bool] = None
    hdmi_2_1: Optional[bool] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    marca_preferida: Optional[str] = None
    categoria_foco: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    alternativa_ofrecida: Optional[str] = None
    genero_declarado: Optional[str] = None
    sku_foco: Optional[str] = None
    frustracion_acumulada: int = 0
    presupuesto_min_buscado: Optional[float] = None
    atributos: Optional[dict] = None
    atributos_texto: Optional[str] = None


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
    refresh_hz_min: Optional[int] = None
    bateria_mah_min: Optional[int] = None
    camara_mp_min: Optional[int] = None
    potencia_w_min: Optional[int] = None
    capacidad_kg_min: Optional[float] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    inverter: Optional[bool] = None
    no_frost: Optional[bool] = None
    smart_tv: Optional[bool] = None
    bluetooth_incluido: Optional[bool] = None
    nfc: Optional[bool] = None
    usb_c: Optional[bool] = None
    hdmi_2_1: Optional[bool] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    marca_preferida: Optional[str] = None
    categoria_foco: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    alternativa_ofrecida: Optional[str] = None
    genero_declarado: Optional[str] = None
    sku_foco: Optional[str] = None
    frustracion_acumulada: int = 0
    presupuesto_min_buscado: Optional[float] = None
