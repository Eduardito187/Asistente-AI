from app.application.services.detector_contacto_cliente import (
    DetectorContactoCliente,
)


def test_detecta_email():
    c = DetectorContactoCliente.detectar("mi email es eduardo@gmail.com gracias")
    assert c.email == "eduardo@gmail.com"


def test_detecta_telefono_boliviano():
    c = DetectorContactoCliente.detectar("mi numero es 70123456")
    assert c.telefono is not None


def test_detecta_telefono_con_codigo_pais():
    c = DetectorContactoCliente.detectar("contactame al +591 70123456")
    assert c.telefono is not None


def test_sin_contacto_devuelve_none():
    c = DetectorContactoCliente.detectar("hola necesito una laptop")
    assert c.email is None
    assert c.telefono is None


def test_vacio():
    c = DetectorContactoCliente.detectar("")
    assert c.email is None
