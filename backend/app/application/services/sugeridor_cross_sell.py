from __future__ import annotations

from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery

MAPEO_CROSS_SELL: dict[str, tuple[tuple[str, str], ...]] = {
    "laptops": (
        ("accesorios laptop", "mochila"),
        ("accesorios laptop", "mouse"),
    ),
    "computacion": (
        ("accesorios laptop", "mouse"),
        ("accesorios laptop", "teclado"),
    ),
    "celulares": (
        ("accesorios celular", "funda"),
        ("accesorios celular", "cargador"),
    ),
    "televisores": (
        ("audio", "soundbar"),
        ("accesorios tv", "soporte pared"),
    ),
    "audio": (
        ("audio", "cable audio"),
    ),
    "electrodomesticos": (
        ("hogar", "accesorios cocina"),
    ),
}

MAX_SUGERENCIAS = 2


class SugeridorCrossSell:
    """SRP: dado un producto recien agregado/cerrado, sugerir complementos.

    Usa un mapeo categoria -> (categoria_objetivo, query) y llama
    buscar_productos con filtros seguros. Es determinista: sin LLM."""

    def __init__(self, buscar: BuscarProductosHandler) -> None:
        self._buscar = buscar

    def sugerir(self, categoria_origen: str | None, skus_excluir: set[str]) -> list[dict]:
        clave = (categoria_origen or "").strip().lower()
        reglas = MAPEO_CROSS_SELL.get(clave)
        if not reglas:
            return []
        vistos: set[str] = set(skus_excluir or set())
        sugerencias: list[dict] = []
        for categoria_objetivo, query in reglas:
            if len(sugerencias) >= MAX_SUGERENCIAS:
                break
            productos = self._buscar.ejecutar(
                BuscarProductosQuery(
                    query=query,
                    categoria=categoria_objetivo,
                    solo_con_stock=True,
                )
            )
            for p in productos:
                if str(p.sku) in vistos:
                    continue
                sugerencias.append(
                    {
                        "sku": str(p.sku),
                        "nombre": p.nombre,
                        "precio_bob": float(p.precio.monto),
                        "categoria": p.categoria or "",
                    }
                )
                vistos.add(str(p.sku))
                break
        return sugerencias
