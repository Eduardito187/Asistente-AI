from app.application.services.deduplicador_variantes import DeduplicadorVariantes
from tests._fakes import FakePrecio, FakeProducto


def _p(sku, nombre, ram, ssd, precio, marca="asus", subcat="laptops"):
    return FakeProducto(
        sku=sku, nombre=nombre, ram_gb=ram, capacidad_gb=ssd,
        precio=FakePrecio(precio), marca=marca, subcategoria=subcat,
    )


def test_variante_de_misma_familia_se_dedup():
    a = _p("A", "Asus Vivobook X515 (8+256gb)", 8, 256, 5000)
    b = _p("B", "Asus Vivobook X515 (16+512gb)", 16, 512, 7000)
    out = DeduplicadorVariantes.deduplicar([a, b])
    assert len(out) == 1
    assert out[0].sku == "B"


def test_familias_distintas_se_preservan():
    a = _p("A", "Asus Vivobook X515 (8+256gb)", 8, 256, 5000)
    b = _p("B", "Asus Vivobook X1504 (16+512gb)", 16, 512, 6500)
    out = DeduplicadorVariantes.deduplicar([a, b])
    assert len(out) == 2


def test_lista_unica_pasa_intacta():
    a = _p("A", "Asus Vivobook X515", 8, 256, 5000)
    out = DeduplicadorVariantes.deduplicar([a])
    assert out == [a]


def test_lista_vacia():
    assert DeduplicadorVariantes.deduplicar([]) == []
