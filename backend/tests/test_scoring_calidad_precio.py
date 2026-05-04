from app.application.services.scoring_calidad_precio import ScoringCalidadPrecio
from tests._fakes import FakePrecio, FakeProducto


def test_mejor_relacion_calidad_precio():
    productos = [
        FakeProducto(
            sku="caro", nombre="HP Premium", procesador="i7-13700H",
            ram_gb=16, capacidad_gb=512, gpu="GeForce RTX 4060",
            precio=FakePrecio(15000),
        ),
        FakeProducto(
            sku="medio", nombre="Acer Nitro V", procesador="i5-13420H",
            ram_gb=16, capacidad_gb=512, gpu="GeForce RTX 5050",
            precio=FakePrecio(8799),
        ),
        FakeProducto(
            sku="barato", nombre="Vivobook i3", procesador="i3-1215U",
            ram_gb=8, capacidad_gb=256, precio=FakePrecio(5500),
        ),
    ]
    ranking = ScoringCalidadPrecio.calcular(productos)
    assert ranking[0].rank == 1
    # El medio (Acer Nitro V con GPU) deberia tener mejor ratio que el caro
    medio = next(r for r in ranking if r.sku == "medio")
    caro = next(r for r in ranking if r.sku == "caro")
    assert medio.ratio > caro.ratio


def test_lista_vacia():
    assert ScoringCalidadPrecio.calcular([]) == []
