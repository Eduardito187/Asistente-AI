from app.application.services.generador_trade_offs import GeneradorTradeOffs
from tests._fakes import FakePrecio, FakeProducto


def _p(sku, ram, ssd, precio, gpu=None):
    return FakeProducto(sku=sku, nombre=f"prod {sku}", ram_gb=ram, capacidad_gb=ssd, precio=FakePrecio(precio), gpu=gpu)


def test_principal_con_gpu_unica_gana():
    principal = _p("A", 16, 512, 8500, gpu="GeForce RTX 5050")
    alt = [_p("B", 16, 512, 7500), _p("C", 16, 512, 7000)]
    t = GeneradorTradeOffs.comparar(principal, alt)
    assert any("GPU" in g for g in t.gana)


def test_principal_mas_caro_pierde():
    principal = _p("A", 16, 512, 12000)
    alt = [_p("B", 16, 512, 8000)]
    t = GeneradorTradeOffs.comparar(principal, alt)
    assert any("caro" in pp.lower() or "más" in pp for pp in t.pierde)


def test_sin_alternativas_resumen_unico():
    principal = _p("A", 16, 512, 8000)
    t = GeneradorTradeOffs.comparar(principal, [])
    assert "unica" in t.resumen.lower()
