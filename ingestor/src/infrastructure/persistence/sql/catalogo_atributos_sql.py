from __future__ import annotations


class CatalogoAtributosSql:
    """SQL para registrar qué atributos dinámicos existen por categoría/subcategoría."""

    UPSERT = """
    INSERT INTO catalogo_atributos (categoria, subcategoria, nombre)
    VALUES (:categoria, :subcategoria, :nombre)
    ON DUPLICATE KEY UPDATE conteo_productos = conteo_productos + 1
    """
