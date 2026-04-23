from __future__ import annotations

from typing import Optional

from ...domain.productos import Producto
from .extractor_specs_producto import ExtractorSpecsProducto


class ComparadorProductos:
    """SRP: dado un listado de productos (2-4), construye una tabla
    comparativa estructurada + una conclusión (mejor general, mejor
    precio/calidad, más económica) según el tipo de producto.

    No usa LLM: es determinista. El LLM solo formatea la salida."""

    # Qué atributos mostrar por subcategoría (orden importa: primeros más relevantes)
    _ATRIBUTOS_POR_SUBCATEGORIA: dict[str, tuple[tuple[str, str], ...]] = {
        "Smartphones": (
            ("ram_gb", "RAM"),
            ("almacenamiento_gb", "Almacenamiento"),
            ("pulgadas", "Pantalla"),
            ("camara_mp", "Cámara principal"),
            ("camara_frontal_mp", "Cámara frontal"),
            ("bateria_mah", "Batería"),
            ("procesador", "Procesador"),
            ("soporta_5g", "5G"),
            ("sistema_operativo", "Sistema"),
        ),
        "Smartwatch": (
            ("pulgadas", "Pantalla"),
            ("bateria_mah", "Batería"),
            ("sistema_operativo", "Sistema"),
            ("color", "Color"),
        ),
        "Smart TV": (
            ("pulgadas", "Pulgadas"),
            ("resolucion", "Resolución"),
            ("tipo_panel", "Tipo de panel"),
            ("refresh_hz", "Tasa de refresco"),
            ("sistema_operativo", "Sistema"),
        ),
        "Notebooks": (
            ("procesador", "Procesador"),
            ("ram_gb", "RAM"),
            ("almacenamiento_gb", "Almacenamiento"),
            ("pulgadas", "Pantalla"),
            ("sistema_operativo", "Sistema"),
        ),
        "Lavadoras": (
            ("capacidad_kg", "Capacidad (kg)"),
            ("potencia_w", "Potencia"),
            ("es_electrico", "Eléctrica"),
            ("color", "Color"),
        ),
    }

    # Atributos genéricos cuando no hay regla de subcategoría
    _ATRIBUTOS_GENERICOS: tuple[tuple[str, str], ...] = (
        ("pulgadas", "Pulgadas"),
        ("potencia_w", "Potencia"),
        ("capacidad_litros", "Capacidad (L)"),
        ("capacidad_kg", "Capacidad (kg)"),
        ("procesador", "Procesador"),
        ("color", "Color"),
    )

    _COMUNES = (
        ("marca", "Marca"),
        ("precio_bob", "Precio actual"),
        ("precio_anterior_bob", "Precio anterior"),
    )

    @classmethod
    def comparar(cls, productos: list[Producto]) -> dict:
        if len(productos) < 2:
            return {"tabla": {"skus": [], "filas": []}, "conclusion": None}
        specs = [ExtractorSpecsProducto.extraer(p) for p in productos]
        subcats = {s.get("subcategoria") for s in specs if s.get("subcategoria")}
        subcat = next(iter(subcats)) if len(subcats) == 1 else None
        atributos = cls._ATRIBUTOS_POR_SUBCATEGORIA.get(subcat or "", cls._ATRIBUTOS_GENERICOS)
        filas = [
            cls._fila(titulo, [cls._formatear(s.get(clave), clave) for s in specs])
            for clave, titulo in (*cls._COMUNES, *atributos)
        ]
        return {
            "tabla": {
                "skus": [s["sku"] for s in specs],
                "nombres": [s["nombre"] for s in specs],
                "filas": filas,
            },
            "conclusion": cls._concluir(specs),
        }

    @staticmethod
    def _fila(titulo: str, valores: list[str]) -> dict:
        return {"campo": titulo, "valores": valores}

    _FORMATOS_SIMPLES: dict[str, str] = {
        "ram_gb": "{v} GB",
        "almacenamiento_gb": "{v} GB",
        "bateria_mah": "{v} mAh",
        "camara_mp": "{v} MP",
        "camara_frontal_mp": "{v} MP",
        "refresh_hz": "{v} Hz",
        "potencia_w": "{v} W",
    }

    @classmethod
    def _formatear(cls, valor: object, clave: str) -> str:
        if valor is None or valor == "":
            return "No disponible"
        if clave.endswith("_bob"):
            return f"Bs {int(valor):,}".replace(",", ".")
        if clave == "pulgadas":
            return f"{valor}\""
        if clave == "soporta_5g":
            return "Sí" if valor else "No"
        if clave == "es_electrico":
            return "Sí" if valor else "Gas/Otra"
        plantilla = cls._FORMATOS_SIMPLES.get(clave)
        if plantilla:
            return plantilla.format(v=int(valor))
        return str(valor)

    @classmethod
    def _concluir(cls, specs: list[dict]) -> dict:
        """Decide mejor general / mejor precio-calidad / más económica. Usa
        un score simple: suma ponderada de specs clave normalizadas; para
        precio-calidad divide ese score por el precio."""
        mejor_general = max(specs, key=cls._score_calidad)
        mas_economica = min(specs, key=lambda s: s["precio_bob"])
        precio_calidad = max(
            specs,
            key=lambda s: cls._score_calidad(s) / s["precio_bob"] if s["precio_bob"] > 0 else 0,
        )
        return {
            "mejor_general": {
                "sku": mejor_general["sku"],
                "razon": cls._razon_mejor(mejor_general),
            },
            "mejor_precio_calidad": {
                "sku": precio_calidad["sku"],
                "razon": f"mejor relación specs/precio a Bs {int(precio_calidad['precio_bob'])}",
            },
            "mas_economica": {
                "sku": mas_economica["sku"],
                "razon": f"el más accesible del grupo a Bs {int(mas_economica['precio_bob'])}",
            },
        }

    @staticmethod
    def _score_calidad(s: dict) -> float:
        """Heurística: suma de specs clave (RAM, storage, cámara, batería,
        pulgadas, refresh). Todos los campos None cuentan 0."""
        def v(k: str) -> float:
            x = s.get(k)
            return float(x) if isinstance(x, (int, float)) and x is not None else 0.0
        return (
            v("ram_gb") * 8
            + v("almacenamiento_gb") * 0.3
            + v("camara_mp") * 2
            + v("camara_frontal_mp")
            + v("bateria_mah") * 0.01
            + v("pulgadas") * 10
            + v("refresh_hz") * 0.5
        )

    @staticmethod
    def _razon_mejor(ganador: dict) -> str:
        ventajas: list[str] = []
        if ganador.get("ram_gb"):
            ventajas.append(f"{ganador['ram_gb']} GB RAM")
        if ganador.get("camara_mp"):
            ventajas.append(f"cámara {ganador['camara_mp']} MP")
        if ganador.get("bateria_mah"):
            ventajas.append(f"{ganador['bateria_mah']} mAh")
        if ganador.get("pulgadas"):
            ventajas.append(f'pantalla {ganador["pulgadas"]}"')
        if not ventajas:
            return "mejor combinación de specs del grupo"
        return "lidera en " + ", ".join(ventajas[:3])
