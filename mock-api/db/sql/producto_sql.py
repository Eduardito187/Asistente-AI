from __future__ import annotations


class ProductoSql:
    """Catalogo SQL del mock-api para productos."""

    _SELECT = (
        "SELECT p.sku, p.nombre, p.descripcion, c.nombre AS categoria, m.nombre AS marca, "
        "p.precio_bob, p.precio_anterior_bob, p.stock, p.imagen_url, p.activo "
        "FROM productos p "
        "LEFT JOIN categorias c ON c.id = p.categoria_id "
        "LEFT JOIN marcas m     ON m.id = p.marca_id"
    )

    @classmethod
    def select(cls, where: str = "") -> str:
        w = f" WHERE {where}" if where else ""
        return f"{cls._SELECT}{w} ORDER BY p.id"
