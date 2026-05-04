from app.application.services.detector_cpu_tier import (
    CpuSufijo,
    CpuTier,
    DetectorCpuTier,
)


def test_i5_u_eficiencia():
    info = DetectorCpuTier.detectar("Core i5-1334U")
    assert info.tier == CpuTier.MID
    assert info.sufijo == CpuSufijo.EFICIENCIA


def test_i7_h_rendimiento():
    info = DetectorCpuTier.detectar("Core i7-13700H")
    assert info.tier == CpuTier.HIGH
    assert info.sufijo == CpuSufijo.RENDIMIENTO


def test_i7_u_no_es_alto_rendimiento():
    info = DetectorCpuTier.detectar("Intel Core i7-1355U")
    assert info.tier == CpuTier.HIGH
    assert info.sufijo == CpuSufijo.EFICIENCIA
    assert DetectorCpuTier.es_alto_rendimiento(info) is False


def test_i9_es_flagship():
    info = DetectorCpuTier.detectar("Core i9-13900HS")
    assert info.tier == CpuTier.FLAGSHIP
    assert DetectorCpuTier.es_alto_rendimiento(info) is True


def test_ryzen_7_hs():
    info = DetectorCpuTier.detectar("Ryzen 7 7735HS")
    assert info.tier == CpuTier.HIGH
    assert info.sufijo == CpuSufijo.RENDIMIENTO


def test_celeron_low():
    info = DetectorCpuTier.detectar("Celeron N4500")
    assert info.tier == CpuTier.LOW


def test_core_ultra_7_high():
    info = DetectorCpuTier.detectar("Core Ultra 7 155H")
    assert info.tier == CpuTier.HIGH
    assert info.familia == "Core Ultra 7"


def test_texto_vacio():
    assert DetectorCpuTier.detectar("") is None
    assert DetectorCpuTier.detectar(None) is None
