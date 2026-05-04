from app.application.services.anticipador_preguntas_siguientes import (
    AnticipadorPreguntasSiguientes,
)
from tests._fakes import FakePerfil


def test_sin_uso_pregunta_uso():
    perfil = FakePerfil(categoria_foco="Laptops", presupuesto_max=8000)
    ps = AnticipadorPreguntasSiguientes.sugerir(perfil)
    assert any("usar" in q.lower() or "uso" in q.lower() for q in ps)


def test_sin_presupuesto_pregunta_presupuesto():
    perfil = FakePerfil(categoria_foco="Laptops", uso_declarado="estudio")
    ps = AnticipadorPreguntasSiguientes.sugerir(perfil)
    assert any("presupuesto" in q.lower() for q in ps)


def test_perfil_completo_pregunta_profundizacion():
    perfil = FakePerfil(
        categoria_foco="Laptops", uso_declarado="ingenieria",
        presupuesto_max=11000,
    )
    perfil.marca_preferida = "asus"
    ps = AnticipadorPreguntasSiguientes.sugerir(perfil)
    assert len(ps) > 0
    # Debería sugerir profundización (comparar, accesorios, etc.)
    assert all("presupuesto" not in q.lower() for q in ps)


def test_max_3_sugerencias():
    perfil = FakePerfil()
    ps = AnticipadorPreguntasSiguientes.sugerir(perfil)
    assert len(ps) <= 3
