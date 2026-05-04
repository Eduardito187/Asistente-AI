from app.application.chat.paso_agente import PasoAgente
from app.application.services.sintetizador_respuesta_trace import (
    SintetizadorRespuestaTrace,
)


def test_sintetiza_de_ultimo_buscar():
    trace = [
        PasoAgente(
            tool="buscar_productos",
            args={},
            result={
                "productos": [
                    {"nombre": "HP Victus", "precio_bob": 14549, "sku": "BM4X8UA"},
                    {"nombre": "Acer Nitro", "precio_bob": 8799, "sku": "ACE-NHU1"},
                ],
                "preguntas_siguientes": ["¿Cual es tu presupuesto?"],
            },
        ),
    ]
    out = SintetizadorRespuestaTrace.sintetizar(trace)
    assert "HP Victus" in out
    assert "[BM4X8UA]" in out
    assert "presupuesto" in out


def test_sin_buscar_devuelve_none():
    trace = [PasoAgente(tool="listar_categorias", args={}, result={"categorias": []})]
    assert SintetizadorRespuestaTrace.sintetizar(trace) is None


def test_trace_vacio_devuelve_none():
    assert SintetizadorRespuestaTrace.sintetizar([]) is None


def test_buscar_sin_productos_aun_devuelve_mensaje():
    trace = [PasoAgente(tool="buscar_productos", args={}, result={"productos": []})]
    out = SintetizadorRespuestaTrace.sintetizar(trace)
    assert out is not None
    assert "no" in out.lower() or "ajustamos" in out.lower()


def test_incluye_contradiccion_si_existe():
    trace = [
        PasoAgente(
            tool="buscar_productos",
            args={},
            result={
                "productos": [{"nombre": "x", "precio_bob": 1000, "sku": "A"}],
                "contradiccion_detectada": {
                    "explicacion": "presupuesto bajo para tu uso",
                    "tipo": "test",
                },
            },
        ),
    ]
    out = SintetizadorRespuestaTrace.sintetizar(trace)
    assert "presupuesto bajo" in out
