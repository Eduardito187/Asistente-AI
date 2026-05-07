from app.application.services.clasificador_turno_exitoso import (
    ClasificadorTurnoExitoso,
)


def test_turno_con_productos_y_respuesta_sustancial_es_exitoso():
    out = ClasificadorTurnoExitoso.evaluar(
        mensaje_usuario="quiero una laptop",
        respuesta="Te recomiendo el Acer Nitro V con 16GB RAM, SSD 512GB y RTX 5050 a Bs 8.799 [SKU]. " * 3,
        productos_citados=[{"sku": "X"}, {"sku": "Y"}],
        ruta="agente",
        tiempo_ms=5000,
        mentiras_detectadas=0,
    )
    assert out.es_exitoso is True
    assert out.score >= 50


def test_turno_con_mentiras_no_se_cura():
    out = ClasificadorTurnoExitoso.evaluar(
        mensaje_usuario="laptop",
        respuesta="Tiene HDMI 2.1 garantia 5 anios " * 5,
        productos_citados=[{"sku": "X"}],
        ruta="agente",
        tiempo_ms=4000,
        mentiras_detectadas=2,
    )
    assert out.es_exitoso is False


def test_respuesta_corta_no_exitoso():
    out = ClasificadorTurnoExitoso.evaluar(
        mensaje_usuario="laptop",
        respuesta="ok",
        productos_citados=[],
        ruta="agente",
        tiempo_ms=3000,
        mentiras_detectadas=0,
    )
    assert out.es_exitoso is False


def test_atajo_no_se_cura():
    out = ClasificadorTurnoExitoso.evaluar(
        mensaje_usuario="hola",
        respuesta="Hola! En que te puedo ayudar?",
        productos_citados=[],
        ruta="atajo_saludo",
        tiempo_ms=10,
        mentiras_detectadas=0,
    )
    assert out.es_exitoso is False


def test_respuesta_con_canned_no_exitoso():
    out = ClasificadorTurnoExitoso.evaluar(
        mensaje_usuario="x",
        respuesta="se me complico resolver tu consulta. " * 5,
        productos_citados=[],
        ruta="agente",
        tiempo_ms=10000,
        mentiras_detectadas=0,
    )
    assert out.es_exitoso is False
