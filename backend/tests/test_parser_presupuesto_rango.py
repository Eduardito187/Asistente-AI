from app.application.services.parser_presupuesto import ParserPresupuesto


def test_rango_ideal_y_max_separado():
    texto = "Mi presupuesto ideal es 8500 Bs, pero podria subir hasta 11000 Bs si vale la pena"
    ideal, techo = ParserPresupuesto.extraer_rango(texto)
    assert ideal == 8500.0
    assert techo == 11000.0


def test_solo_un_numero_es_techo():
    texto = "tengo presupuesto de 6000 Bs"
    ideal, techo = ParserPresupuesto.extraer_rango(texto)
    assert ideal is None
    assert techo == 6000.0


def test_orden_invertido_se_normaliza():
    texto = "preferiblemente 11000 pero hasta 8500 si no encuentro mejor"
    ideal, techo = ParserPresupuesto.extraer_rango(texto)
    assert ideal == 8500.0
    assert techo == 11000.0


def test_sin_numero_devuelve_par_none():
    ideal, techo = ParserPresupuesto.extraer_rango("hola")
    assert ideal is None
    assert techo is None
