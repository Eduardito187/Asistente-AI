from app.application.services.extractor_termino_no_resuelto import (
    ExtractorTerminoNoResuelto,
)


def test_extrae_palabra_larga_no_stopword():
    t = ExtractorTerminoNoResuelto.extraer("necesito una refrigeradora")
    assert t == "refrigeradora"


def test_ignora_stopwords():
    t = ExtractorTerminoNoResuelto.extraer("para mi ayuda")
    assert t is None


def test_ignora_palabras_cortas():
    t = ExtractorTerminoNoResuelto.extraer("ok no si")
    assert t is None


def test_vacio():
    assert ExtractorTerminoNoResuelto.extraer("") is None
    assert ExtractorTerminoNoResuelto.extraer(None) is None


def test_palabra_mas_larga_gana():
    t = ExtractorTerminoNoResuelto.extraer("busco hidrolavadora industrial")
    assert t in ("hidrolavadora", "industrial")
