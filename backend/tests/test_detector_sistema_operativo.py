from app.application.services.detector_sistema_operativo_producto import (
    DetectorSistemaOperativoProducto,
)
from tests._fakes import FakeProducto


def test_freedos_advierte_no_bloquea():
    p = FakeProducto(sku="x", nombre="Notebook ASUS i5 (8+ 512gb) FreeDOS")
    adv = DetectorSistemaOperativoProducto.detectar(p)
    assert adv is not None
    assert adv.so_detectado == "FreeDOS"
    assert adv.bloquea_uso_profesional is False


def test_chromebook_bloquea_uso_profesional():
    p = FakeProducto(sku="x", nombre="Lenovo Chromebook 4GB/32GB eMMC")
    adv = DetectorSistemaOperativoProducto.detectar(p)
    assert adv is not None
    assert adv.so_detectado == "ChromeOS"
    assert adv.bloquea_uso_profesional is True


def test_windows_no_advierte():
    p = FakeProducto(sku="x", nombre="HP Notebook i7 win11 home")
    adv = DetectorSistemaOperativoProducto.detectar(p)
    assert adv is None


def test_chromeos_en_campo_so():
    p = FakeProducto(sku="x", nombre="Notebook generico", sistema_operativo="ChromeOS")
    adv = DetectorSistemaOperativoProducto.detectar(p)
    assert adv is not None
    assert adv.bloquea_uso_profesional is True
