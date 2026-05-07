"""Tests del detector de comparacion explicita.

Caso reportado: 'quiero que me compares un iphone 17 pro max y un s26 ultra
cual me conviene, soy periodista' debe disparar el flujo deterministico.
Antes el regex solo capturaba 'compara/compáralos' y dejaba pasar 'compares'."""
from app.application.services.detector_comparacion_explicita import (
    DetectorComparacionExplicita,
)


def test_compares_dispara_deteccion():
    out = DetectorComparacionExplicita.detectar(
        "quiero que me compares un iphone 17 pro max y un s26 ultra"
    )
    assert out is not None
    assert len(out.fragmentos) == 2
    assert "iphone" in out.fragmentos[0].lower()
    assert "s26" in out.fragmentos[1].lower()


def test_compara_clasica():
    out = DetectorComparacionExplicita.detectar(
        "comparame el iphone 17 pro max y el s26 ultra"
    )
    assert out is not None
    assert len(out.fragmentos) >= 2


def test_vs_directo():
    out = DetectorComparacionExplicita.detectar("iphone 17 pro max vs s26 ultra")
    assert out is not None


def test_cual_me_conviene_sin_entre():
    out = DetectorComparacionExplicita.detectar(
        "cual me conviene el iphone 17 pro max y el s26 ultra"
    )
    assert out is not None


def test_quisiera_comparar():
    out = DetectorComparacionExplicita.detectar(
        "quisiera comparar un galaxy s26 y un iphone 17"
    )
    assert out is not None


def test_que_me_compares():
    out = DetectorComparacionExplicita.detectar(
        "quiero que me compares estas dos opciones"
    )
    # 'estas dos opciones' no son fragmentos separables; igual el disparador
    # debe matchear pero el resultado puede ser None por <2 fragmentos.
    assert out is None or len(out.fragmentos) >= 2


def test_no_dispara_para_pregunta_normal():
    assert DetectorComparacionExplicita.detectar("hola que tal") is None
    assert DetectorComparacionExplicita.detectar("necesito una laptop") is None


def test_caso_real_completo_con_contexto_extra():
    """El caso EXACTO del bug reportado por el usuario."""
    out = DetectorComparacionExplicita.detectar(
        "quiero que me compares un iphone 17 pro max y un s26 ultra "
        "cual me conviene, soy periodista"
    )
    assert out is not None, "el detector debe disparar — antes no lo hacia"
    assert len(out.fragmentos) >= 2
    # Los fragmentos deben contener nombres reconocibles
    texto = " ".join(out.fragmentos).lower()
    assert "iphone" in texto
    assert "s26" in texto


def test_diferencia_entre():
    out = DetectorComparacionExplicita.detectar(
        "diferencia entre el iphone 17 pro y el galaxy s26"
    )
    assert out is not None
