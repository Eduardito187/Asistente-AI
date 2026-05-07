"""Tests para los servicios introducidos por el review 2026-05-07.

Cubre las piezas determinísticas (parsers, detectores, render forzados,
post-procesadores). Los bloques al system prompt se testean por la
salida `renderizar()` — verificar que el LLM cumpla la directiva queda
para los harness de conversaciones."""

from __future__ import annotations

import pytest

from app.application.services.ajustador_respuesta_formato import (
    AjustadorRespuestaFormato,
)
from app.application.services.bloque_conclusion_riesgo import BloqueConclusionRiesgo
from app.application.services.bloque_fallback_marca import BloqueFallbackMarca
from app.application.services.bloque_freedos_warning import BloqueFreedosWarning
from app.application.services.bloque_requisitos_nd import BloqueRequisitosND
from app.application.services.bloque_tres_secciones_filtros import (
    BloqueTresSeccionesFiltros,
)
from app.application.services.detector_exclusiones_mensaje import (
    DetectorExclusionesMensaje,
)
from app.application.services.detector_formato_solicitado import (
    DetectorFormatoSolicitado,
)
from app.application.services.detector_frustracion import DetectorFrustracion
from app.application.services.detector_pregunta_tecnica import DetectorPreguntaTecnica
from app.application.services.detector_requisitos_nd_obligatorios import (
    DetectorRequisitosNDObligatorios,
)
from app.application.services.formato_solicitado import FormatoSolicitado
from app.application.services.generador_cierre_contextual import (
    GeneradorCierreContextual,
)
from app.application.services.limpiador_secciones_vacias import (
    LimpiadorSeccionesVacias,
)
from app.application.services.matcher_fuzzy_keywords import MatcherFuzzyKeywords
from app.application.services.parser_productos_pegados import ParserProductosPegados


# ===================== ParserProductosPegados ===========================


def test_parser_pegados_caso_feedback_completo():
    mensaje = (
        "asus tuf f16 i5 16 ram 512 bs 10699 freedos\n"
        "asus x515 i7 16 ram 512 bs 10799\n"
        "hp ryzen 7 16 ram 512 bs 7499\n"
        "lenovo ryzen 7 16 ram 512 bs 6499"
    )
    listado = ParserProductosPegados.parsear(mensaje)
    assert len(listado.productos) == 4
    primero = listado.productos[0]
    assert primero.marca == "Asus"
    assert primero.ram_gb == 16
    assert primero.storage_gb == 512
    assert primero.precio_bob == pytest.approx(10699.0)
    assert primero.sistema_operativo and "freedos" in primero.sistema_operativo.lower()


def test_parser_pegados_un_solo_producto_no_aplica():
    """Un solo producto NO se considera 'listado pegado' — es pregunta normal."""
    listado = ParserProductosPegados.parsear("hola busco asus i7 16gb ram 512 bs 8000")
    assert listado.vacio()


def test_parser_pegados_texto_sin_specs_no_aplica():
    listado = ParserProductosPegados.parsear("hola, como estas?\nbusco una laptop")
    assert listado.vacio()


# ===================== DetectorPreguntaTecnica ==========================


@pytest.mark.parametrize("mensaje,esperado", [
    ("no me vendas humo", True),
    ("si una laptop solo tiene i7 pero no GPU, sirve para civil 3d?", True),
    ("realmente vale la pena?", True),
    ("pasame con un humano", False),
    ("eres un bot inutil", False),
    ("hola", False),
])
def test_detector_pregunta_tecnica(mensaje, esperado):
    assert DetectorPreguntaTecnica.es_pregunta_tecnica(mensaje) is esperado


def test_pidio_humano_explicito_solo_pase_explicito():
    assert DetectorFrustracion.pidio_humano_explicito("pasame con un humano")
    assert DetectorFrustracion.pidio_humano_explicito("dame el whatsapp de ventas")
    # 'no sirve' es false positive del regex viejo, NO es pase explicito.
    assert not DetectorFrustracion.pidio_humano_explicito(
        "este producto no sirve para gaming"
    )


# ===================== DetectorExclusionesMensaje =======================


def test_exclusiones_typos_extremos():
    salida = DetectorExclusionesMensaje.detectar(
        "no qiero chrombuk ni celeron ni lentos"
    )
    assert "chromebook" in salida
    assert "celeron" in salida


def test_exclusiones_no_me_muestres():
    salida = DetectorExclusionesMensaje.detectar(
        "no me muestres pentium ni cromebook"
    )
    assert "pentium" in salida
    assert "chromebook" in salida


def test_exclusiones_refrigerador_excluye_frigobar_y_freezer():
    """Cliente pide 'refri familiar' SIN mencionar frigobar/freezer.
    Por default los excluimos del tipo_producto."""
    tipos = DetectorExclusionesMensaje.tipos_a_excluir(
        "necesito una refrigeradora nueva, somos familia de 6"
    )
    assert "frigobar" in tipos
    assert "freezer" in tipos
    assert "exhibidor" in tipos


def test_exclusiones_refrigerador_si_pide_frigobar_no_excluye():
    """Si el cliente menciona frigobar positivamente, NO lo excluimos."""
    tipos = DetectorExclusionesMensaje.tipos_a_excluir(
        "busco un frigobar para mi oficina"
    )
    assert "frigobar" not in tipos


# ===================== DetectorFormatoSolicitado ========================


def test_formato_comprar_evitar_y_una_frase():
    fmt = DetectorFormatoSolicitado.detectar(
        "dame solo: cual comprar, cual evitar y por que en 1 frase"
    )
    assert fmt.forma == "comprar_evitar"
    assert fmt.max_frases == 1


def test_formato_max_productos_sin_colision_frases():
    fmt = DetectorFormatoSolicitado.detectar("dame solo 2 alternativas")
    assert fmt.max_productos == 2
    assert fmt.max_frases is None  # 'solo N' NO infiere cap de oraciones


def test_formato_seguro_barato_no_choca_con_premium():
    fmt = DetectorFormatoSolicitado.detectar(
        "una economica, una buena y una premium"
    )
    # 'economica + premium' lo cubre `_bloque_formato_tres_opciones` existente;
    # mi detector NO matchea aqui para evitar bloque duplicado.
    assert fmt.forma is None


def test_formato_vacio_para_texto_normal():
    fmt = DetectorFormatoSolicitado.detectar("busco una laptop")
    assert fmt.vacio()


# ===================== AjustadorRespuestaFormato ========================


def test_ajustador_cap_productos():
    fmt = FormatoSolicitado(max_productos=2)
    respuesta = (
        "Estas son las opciones:\n"
        "- Acer Nitro V — Bs 8799 [ACE-001]\n"
        "- HP Victus — Bs 14549 [HPV-001]\n"
        "- Dell Alienware — Bs 15799 [DEL-001]"
    )
    out = AjustadorRespuestaFormato.ajustar(respuesta, fmt)
    assert "[ACE-001]" in out
    assert "[HPV-001]" in out
    assert "[DEL-001]" not in out


def test_ajustador_cap_frases_no_consume_header():
    """Header sin punto NO debe consumir el cap de oraciones."""
    fmt = FormatoSolicitado(max_frases=1)
    respuesta = (
        "Estas son las opciones que te puedo ofrecer:\n"
        "- Acer Nitro V — Bs 8799 [ACE-001]"
    )
    out = AjustadorRespuestaFormato.ajustar(respuesta, fmt)
    assert "[ACE-001]" in out


def test_ajustador_cap_frases_no_aplica_si_forma_estructural():
    """Si fmt.forma define la estructura (comprar/evitar), NO aplicar cap
    global de frases — la estructura ya define las lineas."""
    fmt = FormatoSolicitado(forma="comprar_evitar", max_frases=1)
    respuesta = "Comprar: A.\nEvitar: B.\nPor que: C."
    out = AjustadorRespuestaFormato.ajustar(respuesta, fmt)
    # Las 3 lineas se preservan.
    assert "Comprar:" in out
    assert "Evitar:" in out
    assert "Por que:" in out


# ===================== LimpiadorSeccionesVacias =========================


def test_limpiador_strippa_recomendacion_sin_sku():
    respuesta = (
        "Aca te muestro:\n\n"
        "**Recomendación principal:**\n"
        "- Por qué conviene: necesito mas datos\n\n"
        "**Alternativas:**\n"
        "- Otra opcion: Asus — Bs 4999 [ASUS-X1]"
    )
    out = LimpiadorSeccionesVacias.limpiar(respuesta)
    assert "**Recomendación principal:**" not in out
    assert "[ASUS-X1]" in out


def test_limpiador_no_toca_cuando_todo_valido():
    respuesta = (
        "**Recomendación principal:**\n"
        "- Acer — Bs 8799 [ACE-001]\n"
        "- Por qué conviene: 16GB RAM\n\n"
        "**Alternativas:**\n"
        "- HP — Bs 14549 [HPV-001]"
    )
    out = LimpiadorSeccionesVacias.limpiar(respuesta)
    assert "[ACE-001]" in out
    assert "[HPV-001]" in out
    assert "**Recomendación principal:**" in out


# ===================== GeneradorCierreContextual =========================


def _perfil_completo():
    """Mock minimo: dataclass con los campos que lee el generador."""
    class P:
        presupuesto_max = 9000.0
        marca_preferida = None
        uso_declarado = "ingenieria"
        ram_gb_min = 16
        ssd_gb_min = 512
        gpu_dedicada = True
        pulgadas = None
        categoria_foco = "Laptops"
    return P()


def test_cierre_no_repite_lista_cuando_hay_contexto_completo():
    perfil = _perfil_completo()
    cierre = GeneradorCierreContextual.generar(aviso_fallback=None, perfil=perfil)
    assert "presupuesto, marca, uso" not in cierre
    assert "ingenieria" in cierre
    assert "9000" in cierre


def test_cierre_pregunta_solo_slots_faltantes():
    """Sin uso pero con presupuesto + ram: pregunta solo por uso."""
    class P:
        presupuesto_max = 9000.0
        marca_preferida = None
        uso_declarado = None
        ram_gb_min = 16
        ssd_gb_min = None
        gpu_dedicada = None
        pulgadas = None
        categoria_foco = "Laptops"
    cierre = GeneradorCierreContextual.generar(aviso_fallback=None, perfil=P())
    assert "uso" in cierre.lower()
    # NO debe pedir presupuesto ni marca (cliente no se quejo de eso).
    assert "(presupuesto, marca, uso)" not in cierre


# ===================== Bloques al system prompt =========================


def test_bloque_requisitos_nd_tv_ps5():
    bloque = BloqueRequisitosND.renderizar("tv 65 ps5 hdmi 2.1 120hz")
    assert bloque is not None
    assert "HDMI 2.1" in bloque
    assert "120Hz" in bloque
    assert "No tengo ese dato" in bloque


def test_bloque_freedos_solo_para_laptops():
    assert BloqueFreedosWarning.renderizar("busco una laptop") is not None
    assert BloqueFreedosWarning.renderizar("busco una freidora") is None


def test_bloque_fallback_marca_solo_si_acepta_alternativas():
    bloque = BloqueFallbackMarca.renderizar(
        "celular premium prefiero samsung pero acepto iphone o xiaomi"
    )
    assert bloque is not None
    assert "alternativa" in bloque.lower()


def test_bloque_conclusion_riesgo_se_activa_con_specs():
    bloque = BloqueConclusionRiesgo.renderizar("laptop 16gb ram para autocad")
    assert bloque is not None
    assert "Por que conviene" in bloque
    assert "Riesgo" in bloque
    assert "Trade-off" in bloque


def test_bloque_tres_secciones_se_activa_con_minimo_explicito():
    bloque = BloqueTresSeccionesFiltros.renderizar("lavadora minimo 18kg")
    assert bloque is not None
    assert "Cumple todo" in bloque
    assert "No recomendado" in bloque


# ===================== MatcherFuzzyKeywords =============================


@pytest.mark.parametrize("palabra,esperado", [
    ("chrombuk", "chromebook"),  # 2 chars de diff
    ("celeron", "celeron"),      # exacto
    ("celron", "celeron"),       # 1 char de diff
    ("xyz", None),               # nada en comun
])
def test_matcher_fuzzy_keywords(palabra, esperado):
    diccionario = ("chromebook", "celeron", "pentium")
    assert MatcherFuzzyKeywords.mejor_match(palabra, diccionario, ratio_min=0.74) == esperado


# ===================== DetectorRequisitosNDObligatorios =================


@pytest.mark.parametrize("mensaje,debe_incluir", [
    ("tv ps5", "HDMI 2.1"),
    ("refri inverter", "Inverter (motor)"),
    ("laptop con gpu dedicada", "GPU dedicada (RTX/GTX/Radeon)"),
    ("audifonos con anc", "ANC (cancelacion activa)"),
    ("celular con OIS", "Estabilizacion optica de imagen (OIS)"),
])
def test_requisitos_nd_obligatorios(mensaje, debe_incluir):
    requisitos = DetectorRequisitosNDObligatorios.requisitos(mensaje)
    assert debe_incluir in requisitos
