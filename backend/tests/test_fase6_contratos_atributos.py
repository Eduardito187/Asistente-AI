"""FASE 6: Tests de contrato para la cadena
AtributosMensaje → PerfilSesion → BuscarProductosQuery.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "backend")

from app.application.services.detector_correccion_atributo import DetectorCorreccionAtributo
from app.application.services.extractor_atributos_producto import ExtractorAtributosProducto
from app.application.chat.validador_filtros_duros import ValidadorFiltrosDuros
from app.application.chat.tool_dispatcher import ToolDispatcher
from tests._fakes import FakePerfil


# ─── DetectorCorreccionAtributo ───────────────────────────────────────────

def test_correc_gb_dije_desde():
    c = DetectorCorreccionAtributo.detectar("dije desde 256gb de almacenamiento")
    assert any(x.campo == "capacidad_gb_min" and x.valor == 256 for x in c)

def test_correc_gb_no_coma():
    c = DetectorCorreccionAtributo.detectar("no, 512gb")
    assert any(x.campo == "capacidad_gb_min" and x.valor == 512 for x in c)

def test_correc_ram_explicita():
    c = DetectorCorreccionAtributo.detectar("dije 16 de ram")
    assert any(x.campo == "ram_gb_min" and x.valor == 16 for x in c)

def test_correc_hz():
    c = DetectorCorreccionAtributo.detectar("quiero 120hz de refresco")
    assert any(x.campo == "refresh_hz_min" and x.valor == 120 for x in c)

def test_correc_nfc_prefijo():
    c = DetectorCorreccionAtributo.detectar("o sea con NFC")
    assert any(x.campo == "nfc" and x.valor is True for x in c)

def test_correc_so_android():
    c = DetectorCorreccionAtributo.detectar("quiero android")
    assert any(x.campo == "sistema_operativo" and x.valor == "Android" for x in c)

def test_correc_so_windows():
    c = DetectorCorreccionAtributo.detectar("dije windows para el notebook")
    assert any(x.campo == "sistema_operativo" and x.valor == "Windows" for x in c)

def test_correc_gb_invalido_ignorado():
    c = DetectorCorreccionAtributo.detectar("dije 300gb")
    assert not any(x.campo == "capacidad_gb_min" for x in c)

def test_correc_hz_invalido_ignorado():
    # 75hz no es frecuencia estándar soportada
    c = DetectorCorreccionAtributo.detectar("quiero 75hz")
    assert not any(x.campo == "refresh_hz_min" for x in c)


# ─── ExtractorAtributosProducto ───────────────────────────────────────────

def test_extractor_pulgadas():
    r = ExtractorAtributosProducto.extraer("A1", 'TV Samsung 55 pulgadas 4K')
    assert r.pulgadas == 55.0
    assert "pulgadas" in r.campos_poblados

def test_extractor_ram_y_ssd():
    r = ExtractorAtributosProducto.extraer("A2", "Laptop HP 16GB RAM 512GB SSD")
    assert r.ram_gb == 16
    assert r.capacidad_gb == 512

def test_extractor_hz_y_panel():
    r = ExtractorAtributosProducto.extraer("A3", "Monitor ASUS 144Hz IPS")
    assert r.refresh_hz == 144
    assert r.tipo_panel == "IPS"

def test_extractor_mah():
    r = ExtractorAtributosProducto.extraer("A4", "Xiaomi Redmi Note 5000mAh")
    assert r.bateria_mah == 5000

def test_extractor_potencia():
    r = ExtractorAtributosProducto.extraer("A5", "Licuadora Oster 1500W")
    assert r.potencia_w == 1500

def test_extractor_5g():
    r = ExtractorAtributosProducto.extraer("A6", "Samsung Galaxy A54 5G 128GB")
    assert r.soporta_5g is True

def test_extractor_4k_y_oled():
    r = ExtractorAtributosProducto.extraer("A7", "TV LG 65 pulgadas 4K OLED")
    assert r.resolucion == "4K"
    assert r.tipo_panel == "OLED"

def test_extractor_so_android():
    r = ExtractorAtributosProducto.extraer("A8", "Tablet Android 10 pulgadas 64GB")
    assert r.sistema_operativo == "Android"

def test_extractor_sin_datos():
    r = ExtractorAtributosProducto.extraer("A9", "Alfombra decorativa beige")
    assert r.campos_poblados == []


# ─── ValidadorFiltrosDuros — atributos técnicos sticky ────────────────────

def _p(**kw):
    kw.setdefault("precio", type("P", (), {"monto": 1000})())
    return type("P", (), kw)()

def test_vfd_hz_rechaza_bajo():
    assert not ValidadorFiltrosDuros.cumple(_p(refresh_hz=60), {"refresh_hz_min": 120})

def test_vfd_hz_acepta_igual():
    assert ValidadorFiltrosDuros.cumple(_p(refresh_hz=120), {"refresh_hz_min": 120})

def test_vfd_bateria_rechaza():
    assert not ValidadorFiltrosDuros.cumple(_p(bateria_mah=3000), {"bateria_mah_min": 5000})

def test_vfd_camara_rechaza():
    assert not ValidadorFiltrosDuros.cumple(_p(camara_mp=12), {"camara_mp_min": 50})

def test_vfd_potencia_rechaza():
    assert not ValidadorFiltrosDuros.cumple(_p(potencia_w=800), {"potencia_w_min": 1500})

def test_vfd_potencia_acepta():
    assert ValidadorFiltrosDuros.cumple(_p(potencia_w=2000), {"potencia_w_min": 1500})

def test_vfd_so_rechaza():
    assert not ValidadorFiltrosDuros.cumple(
        _p(sistema_operativo="Windows"), {"sistema_operativo": "Android"}
    )

def test_vfd_so_acepta():
    assert ValidadorFiltrosDuros.cumple(
        _p(sistema_operativo="Android"), {"sistema_operativo": "Android"}
    )


# ─── _filtros_sticky_perfil — fusión perfil → filtros ────────────────────

def test_sticky_propaga_hz():
    f = ToolDispatcher._filtros_sticky_perfil({}, FakePerfil(refresh_hz_min=144))
    assert f["refresh_hz_min"] == 144

def test_sticky_llm_gana_sobre_perfil():
    f = ToolDispatcher._filtros_sticky_perfil({"refresh_hz_min": 120}, FakePerfil(refresh_hz_min=60))
    assert f["refresh_hz_min"] == 120

def test_sticky_propaga_5g():
    f = ToolDispatcher._filtros_sticky_perfil({}, FakePerfil(soporta_5g=True))
    assert f["soporta_5g"] is True

def test_sticky_propaga_so():
    f = ToolDispatcher._filtros_sticky_perfil({}, FakePerfil(sistema_operativo="Windows"))
    assert f["sistema_operativo"] == "Windows"

def test_sticky_tiene_14_campos():
    """Contrato: todos los 14 atributos sticky deben estar en el dict."""
    esperados = {
        "refresh_hz_min", "bateria_mah_min", "camara_mp_min",
        "capacidad_kg_min", "potencia_w_min", "soporta_5g",
        "sistema_operativo", "inverter", "no_frost", "smart_tv",
        "bluetooth_incluido", "nfc", "usb_c", "hdmi_2_1",
    }
    f = ToolDispatcher._filtros_sticky_perfil({}, FakePerfil())
    assert esperados <= f.keys()

def test_sticky_none_perfil_vacio():
    """Perfil vacío → todos None (no activa filtros innecesarios)."""
    f = ToolDispatcher._filtros_sticky_perfil({}, FakePerfil())
    for campo in ("refresh_hz_min", "bateria_mah_min", "soporta_5g", "sistema_operativo"):
        assert f[campo] is None
