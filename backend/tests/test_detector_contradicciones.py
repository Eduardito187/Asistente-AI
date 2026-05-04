from app.application.services.detector_contradicciones_usuario import (
    DetectorContradiccionesUsuario,
)
from tests._fakes import FakePerfil


def test_gpu_con_presupuesto_bajo_es_contradiccion():
    perfil = FakePerfil(
        gpu_dedicada=True, presupuesto_max=4500,
        uso_declarado="gaming",
    )
    perfil.categoria_foco = "Laptops"
    c = DetectorContradiccionesUsuario.detectar(perfil)
    assert c is not None
    assert "GPU" in c.explicacion or "gpu" in c.tipo


def test_ingenieria_con_3000_es_contradiccion():
    perfil = FakePerfil(uso_declarado="ingenieria", presupuesto_max=3000)
    perfil.categoria_foco = "Laptops"
    c = DetectorContradiccionesUsuario.detectar(perfil)
    assert c is not None


def test_perfil_normal_no_contradice():
    perfil = FakePerfil(presupuesto_max=8500, uso_declarado="estudio")
    perfil.categoria_foco = "Laptops"
    c = DetectorContradiccionesUsuario.detectar(perfil)
    assert c is None


def test_sin_presupuesto_no_evalua():
    perfil = FakePerfil(gpu_dedicada=True, uso_declarado="render")
    perfil.categoria_foco = "Laptops"
    assert DetectorContradiccionesUsuario.detectar(perfil) is None
