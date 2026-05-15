from __future__ import annotations

import re
from typing import NamedTuple

# El tipo Producto se importa desde el dominio - ajustar si es necesario
# Usamos duck typing: el objeto debe tener .nombre, .sku, .precio_bob

_RX_VARIANTE = re.compile(
    r"\s*[-–]?\s*(?:"
    r"\d+\s*(?:gb|tb|mb)\b"          # capacidad
    r"|(?:negro|blanco|azul|rojo|gris|dorado|plateado|verde|morado|rosa|"
    r"grafito|midnight|starlight|coral|champagne|lavanda|titanio)\b"  # colores
    r"|(?:pro|plus|max|ultra|lite|se|mini|neo|edge)\b"               # variantes de modelo
    r")",
    re.IGNORECASE,
)


class GrupoProducto(NamedTuple):
    modelo_base: str          # nombre sin variante
    representante: object     # el producto con mejor precio o primero
    variantes: list           # todos los productos del grupo
    tiene_variantes: bool     # True si hay más de 1


class AgrupadorVariantesProducto:
    """Agrupa productos por modelo base eliminando sufijos de color/capacidad.

    Ejemplo: ['Samsung A54 128GB Negro', 'Samsung A54 128GB Azul', 'Samsung A54 256GB']
    → 1 grupo 'Samsung A54' con 3 variantes.

    Útil para mostrar opciones sin abrumar con el mismo modelo en varios colores."""

    @classmethod
    def agrupar(cls, productos: list) -> list[GrupoProducto]:
        """Agrupa y retorna lista de GrupoProducto ordenada por precio del representante."""
        grupos: dict[str, list] = {}
        for p in productos:
            base = cls._modelo_base(getattr(p, "nombre", str(p)))
            grupos.setdefault(base, []).append(p)

        resultado: list[GrupoProducto] = []
        for modelo_base, variantes in grupos.items():
            # Representante: el de menor precio
            representante = min(variantes, key=lambda x: float(getattr(x, "precio_bob", 0) or 0))
            resultado.append(GrupoProducto(
                modelo_base=modelo_base,
                representante=representante,
                variantes=variantes,
                tiene_variantes=len(variantes) > 1,
            ))

        # Ordenar por precio del representante
        return sorted(resultado, key=lambda g: float(getattr(g.representante, "precio_bob", 0) or 0))

    @classmethod
    def _modelo_base(cls, nombre: str) -> str:
        """Extrae el nombre base eliminando sufijos de variante."""
        return _RX_VARIANTE.sub("", nombre).strip().rstrip("-–").strip()

    @classmethod
    def texto_variantes(cls, grupo: GrupoProducto) -> str:
        """Genera texto de variantes disponibles para mostrar al cliente."""
        if not grupo.tiene_variantes:
            return ""
        variantes_txt = []
        for v in grupo.variantes:
            nombre = getattr(v, "nombre", "")
            precio = getattr(v, "precio_bob", None)
            precio_txt = f" (Bs {precio:.0f})" if precio else ""
            variantes_txt.append(f"  - {nombre}{precio_txt}")
        return "Variantes disponibles:\n" + "\n".join(variantes_txt)
