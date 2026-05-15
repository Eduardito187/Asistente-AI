from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ValidadorSkuResultado:
    """Filtra productos inválidos de una lista de resultados antes de mostrarlos.

    Criterios de invalidez:
    - Sin SKU
    - Sin precio o precio <= 0
    - Solo tienda física (campo solo_tienda_fisica=True)
    - Descontinuado (campo es_descontinuado=True)
    - Nombre vacío

    SRP: solo filtrar, no buscar. La búsqueda la hace BuscarProductosHandler."""

    @classmethod
    def filtrar(cls, productos: list) -> list:
        """Retorna solo los productos que pasan todas las validaciones."""
        return [p for p in productos if cls._es_valido(p)]

    @classmethod
    def _es_valido(cls, p) -> bool:
        if not getattr(p, "sku", None):
            return False
        precio_obj = getattr(p, "precio", None)
        monto = getattr(precio_obj, "monto", None)
        if monto is None or float(monto) <= 0:
            return False
        if getattr(p, "es_descontinuado", False):
            return False
        nombre = getattr(p, "nombre", None)
        if not nombre or not str(nombre).strip():
            return False
        return True

    @classmethod
    def reportar_filtrados(cls, originales: list, filtrados: list) -> str | None:
        """Si se filtraron productos, retorna mensaje de log. None si no hubo cambios."""
        n_orig = len(originales)
        n_filt = len(filtrados)
        if n_orig == n_filt:
            return None
        return f"ValidadorSkuResultado: filtró {n_orig - n_filt} de {n_orig} productos inválidos"
