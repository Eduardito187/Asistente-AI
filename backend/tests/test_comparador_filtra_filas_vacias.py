"""Verifica que la tabla comparativa NO muestre filas donde TODOS los
productos tienen 'No disponible' (caso real reportado por el usuario)."""
from app.application.services.comparador_productos import ComparadorProductos


def test_filtra_filas_donde_todos_no_disponible():
    filas = [
        {"campo": "Marca", "valores": ["HP", "Dell", "Acer"]},
        {"campo": "Bateria", "valores": ["No disponible", "No disponible", "No disponible"]},
        {"campo": "Pantalla", "valores": ["15.6\"", "16.0\"", "15.6\""]},
    ]
    out = ComparadorProductos._filtrar_filas_sin_datos(filas)
    titulos = [f["campo"] for f in out]
    assert "Bateria" not in titulos
    assert "Marca" in titulos
    assert "Pantalla" in titulos


def test_mantiene_fila_si_al_menos_uno_tiene_dato():
    filas = [
        {"campo": "GPU", "valores": ["RTX 4050", "No disponible", "No disponible"]},
    ]
    out = ComparadorProductos._filtrar_filas_sin_datos(filas)
    assert len(out) == 1
    assert out[0]["campo"] == "GPU"


def test_lista_vacia():
    assert ComparadorProductos._filtrar_filas_sin_datos([]) == []


def test_todas_las_filas_completas_se_mantienen():
    filas = [
        {"campo": "Marca", "valores": ["HP", "Dell"]},
        {"campo": "Procesador", "valores": ["i7", "i5"]},
    ]
    out = ComparadorProductos._filtrar_filas_sin_datos(filas)
    assert len(out) == 2
