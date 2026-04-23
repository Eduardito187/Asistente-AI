from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AtributosProducto:
    """VO inmutable con los atributos estructurados extraidos de un producto.

    Todos los campos son opcionales: un producto dado solo expone los que
    aplican a su categoria (pulgadas para TVs, capacidad_kg para lavadoras,
    etc.). Campos ausentes quedan None y no contaminan los filtros."""

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
    # Specs que habilitan comparaciones ricas sin depender de parse LLM.
    bateria_mah: Optional[int] = None
    camara_mp: Optional[int] = None
    camara_frontal_mp: Optional[int] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    refresh_hz: Optional[int] = None
    gpu: Optional[str] = None
