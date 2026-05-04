from app.application.services.detector_gama_producto import (
    DetectorGamaProducto,
    GamaProducto,
)
from tests._fakes import FakeProducto


def test_celeron_es_entrada():
    p = FakeProducto(sku="x", nombre="Vivobook Go Celeron N4500", procesador="Celeron N4500", ram_gb=4)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.ENTRADA


def test_chromebook_es_entrada():
    p = FakeProducto(sku="x", nombre="Lenovo Chromebook 4GB/32GB eMMC", ram_gb=4, capacidad_gb=32)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.ENTRADA


def test_emmc_es_entrada():
    p = FakeProducto(sku="x", nombre="Notebook 4+64gb eMMC", ram_gb=4, capacidad_gb=64)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.ENTRADA


def test_i5_16gb_512_es_intermedio():
    p = FakeProducto(sku="x", nombre="Asus Vivobook i5", procesador="Intel Core i5-1334U", ram_gb=16, capacidad_gb=512)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.INTERMEDIO


def test_i7_16gb_es_potente():
    p = FakeProducto(sku="x", nombre="HP Pavilion i7", procesador="Core i7-13700H", ram_gb=16, capacidad_gb=512)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.POTENTE


def test_rtx_es_gamer():
    p = FakeProducto(
        sku="x", nombre="HP Victus RTX 5050", procesador="Ryzen 7 7445HS",
        ram_gb=16, capacidad_gb=512, gpu="GeForce RTX 5050",
    )
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.GAMER


def test_quadro_es_workstation():
    p = FakeProducto(sku="x", nombre="Dell Precision Quadro", gpu="Quadro RTX A2000", ram_gb=32)
    assert DetectorGamaProducto.clasificar(p) == GamaProducto.WORKSTATION


def test_apto_uso_profesional():
    intermedio = FakeProducto(sku="x", nombre="i5 16/512", procesador="Core i5-1334U", ram_gb=16, capacidad_gb=512)
    entrada = FakeProducto(sku="x", nombre="Celeron 4/64", procesador="Celeron N4500", ram_gb=4)
    assert DetectorGamaProducto.es_apto_para_uso_profesional(intermedio) is True
    assert DetectorGamaProducto.es_apto_para_uso_profesional(entrada) is False
