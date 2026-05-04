from app.application.services.normalizador_acentos_respuesta import (
    NormalizadorAcentosRespuesta,
)


def test_corrige_palabras_comunes():
    out = NormalizadorAcentosRespuesta.normalizar("contame que te importa mas, te muestro el catalogo tecnico")
    assert "más" in out
    assert "catálogo" in out
    assert "técnico" in out


def test_preserva_caja_inicial():
    out = NormalizadorAcentosRespuesta.normalizar("Mas opciones aqui")
    assert "Más" in out
    assert "aquí" in out


def test_no_toca_voseo():
    texto = "contame que necesitas — vos sabes bien"
    out = NormalizadorAcentosRespuesta.normalizar(texto)
    assert "contame" in out
    assert "vos" in out


def test_vacio_pasa_intacto():
    assert NormalizadorAcentosRespuesta.normalizar("") == ""
    assert NormalizadorAcentosRespuesta.normalizar(None) is None
