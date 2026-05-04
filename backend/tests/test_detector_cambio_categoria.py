from app.application.services.detector_cambio_categoria import DetectorCambioCategoria


def test_ahora_quiero_otra_cosa():
    assert DetectorCambioCategoria.hay_cambio("ahora quiero una TV") is True


def test_mejor_un_celular():
    assert DetectorCambioCategoria.hay_cambio("mejor un celular") is True


def test_olvida_lo_anterior():
    assert DetectorCambioCategoria.hay_cambio("olvida eso, busquemos otra cosa") is True


def test_simple_refinamiento_no_cambia():
    assert DetectorCambioCategoria.hay_cambio("necesito 16GB de RAM") is False


def test_vacio():
    assert DetectorCambioCategoria.hay_cambio("") is False
    assert DetectorCambioCategoria.hay_cambio(None) is False
