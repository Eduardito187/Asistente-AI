from app.application.services.motor_personalidad_dismi import (
    MotorPersonalidadDismi,
    TonoDismi,
)
from tests._fakes import FakePerfil


def test_listo_para_comprar_es_directo():
    perfil = FakePerfil()
    tono = MotorPersonalidadDismi.elegir_tono("ya esta, lo llevo", "estudiante", perfil)
    assert tono == TonoDismi.DIRECTO_DECIDIDO


def test_confundido_es_empatico():
    perfil = FakePerfil()
    tono = MotorPersonalidadDismi.elegir_tono("no se que comprar, ayudame", "generico", perfil)
    assert tono == TonoDismi.EMPATICO_PACIENTE


def test_premium_es_asesor_premium():
    perfil = FakePerfil(presupuesto_max=15000)
    perfil.desired_tier = "flagship"
    tono = MotorPersonalidadDismi.elegir_tono("quiero una laptop", "profesional", perfil)
    assert tono == TonoDismi.ASESOR_PREMIUM


def test_profesional_es_conciso():
    perfil = FakePerfil(presupuesto_max=8000)
    tono = MotorPersonalidadDismi.elegir_tono("necesito laptop para autocad", "profesional", perfil)
    assert tono == TonoDismi.PROFESIONAL_CONCISO


def test_generico_es_amigable():
    perfil = FakePerfil()
    tono = MotorPersonalidadDismi.elegir_tono("hola", "generico", perfil)
    assert tono == TonoDismi.AMIGABLE_CASUAL


def test_guia_no_vacia():
    for tono in TonoDismi:
        guia = MotorPersonalidadDismi.guia_para_prompt(tono)
        assert len(guia) > 20
