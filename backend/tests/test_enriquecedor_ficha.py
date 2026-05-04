from app.application.services.enriquecedor_atributos_ficha import (
    EnriquecedorAtributosFichaIncompleta,
)


from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FichaProducto:
    """Frozen dataclass mirroring Producto (replace requires frozen+slots-friendly)."""
    sku: str
    nombre: str
    gpu: Optional[str] = None
    ram_gb: Optional[int] = None
    capacidad_gb: Optional[int] = None
    descripcion: Optional[str] = None
    descripcion_extendida: Optional[str] = None
    caracteristicas: Optional[str] = None


def test_extrae_gpu_de_descripcion_cuando_falta():
    p = FichaProducto(
        sku="X", nombre="HP Pavilion",
        descripcion="Laptop con GeForce RTX 4060 dedicada",
    )
    out = EnriquecedorAtributosFichaIncompleta.enriquecer(p)
    assert out.gpu and "RTX 4060" in out.gpu.upper()


def test_extrae_ram_de_caracteristicas():
    p = FichaProducto(
        sku="X", nombre="Asus Vivobook",
        caracteristicas="16GB de RAM DDR5",
    )
    out = EnriquecedorAtributosFichaIncompleta.enriquecer(p)
    assert out.ram_gb == 16


def test_no_pisa_valor_existente():
    p = FichaProducto(
        sku="X", nombre="HP", gpu="GeForce GTX 1650",
        descripcion="Tambien dice RTX 4090 en descripcion",
    )
    out = EnriquecedorAtributosFichaIncompleta.enriquecer(p)
    assert "1650" in out.gpu


def test_sin_match_devuelve_mismo_objeto():
    p = FichaProducto(sku="X", nombre="Generic", descripcion="Sin specs")
    out = EnriquecedorAtributosFichaIncompleta.enriquecer(p)
    assert out is p
