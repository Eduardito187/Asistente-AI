from app.application.services.detector_perfil_comprador import (
    DetectorPerfilComprador,
    PerfilComprador,
)


def test_gamer():
    assert DetectorPerfilComprador.detectar("para jugar fortnite") == PerfilComprador.GAMER
    assert DetectorPerfilComprador.detectar("ps5 y xbox") == PerfilComprador.GAMER


def test_estudiante():
    assert DetectorPerfilComprador.detectar("para la universidad") == PerfilComprador.ESTUDIANTE
    assert DetectorPerfilComprador.detectar("estudio mucho") == PerfilComprador.ESTUDIANTE


def test_profesional():
    assert DetectorPerfilComprador.detectar("autocad civil 3d") == PerfilComprador.PROFESIONAL
    assert DetectorPerfilComprador.detectar("para teletrabajo") == PerfilComprador.PROFESIONAL


def test_regalo():
    assert DetectorPerfilComprador.detectar("para mi novia de cumpleanios") == PerfilComprador.REGALO
    assert DetectorPerfilComprador.detectar("regalo de aniversario") == PerfilComprador.REGALO


def test_hogar():
    assert DetectorPerfilComprador.detectar("para la familia ver netflix") == PerfilComprador.HOGAR


def test_empresa():
    assert DetectorPerfilComprador.detectar("equipos para mi oficina") == PerfilComprador.EMPRESA


def test_generico():
    assert DetectorPerfilComprador.detectar("hola") == PerfilComprador.GENERICO


def test_hook_no_vacio():
    hook = DetectorPerfilComprador.hook_recomendacion(PerfilComprador.GAMER)
    assert "GPU" in hook or "gaming" in hook.lower()
