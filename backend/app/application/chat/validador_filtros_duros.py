from __future__ import annotations


class ValidadorFiltrosDuros:
    """Valida que un producto candidato cumpla las restricciones obligatorias
    del turno (categoria, rango de precio, pulgadas, atributos estructurados).

    Unica responsabilidad: decidir si un Producto pasa o no el filtro duro.
    Se usa para cortar candidatos semanticos que aparecen fuera del contexto
    comercial (ej: power bank de 30000mAh cuando el cliente busca TV)."""

    _MINIMOS = (
        ("capacidad_gb_min", "capacidad_gb"),
        ("ram_gb_min", "ram_gb"),
        ("capacidad_litros_min", "capacidad_litros"),
        ("capacidad_kg_min", "capacidad_kg"),
        ("potencia_w_min", "potencia_w"),
    )
    _IGUALES = (
        ("procesador", "procesador"),
        ("tipo_panel", "tipo_panel"),
        ("resolucion", "resolucion"),
        ("color", "color"),
    )
    _TOLERANCIA_PULGADAS = 0.5

    @classmethod
    def cumple(cls, p, filtros: dict) -> bool:
        return (
            cls._cumple_textuales(p, filtros)
            and cls._cumple_precio(p, filtros)
            and cls._cumple_pulgadas(p, filtros)
            and cls._cumple_minimos(p, filtros)
            and cls._cumple_potencia_max(p, filtros)
            and cls._cumple_iguales(p, filtros)
        )

    @staticmethod
    def _cumple_textuales(p, filtros: dict) -> bool:
        categoria = filtros.get("categoria")
        if categoria and categoria.lower() not in (p.categoria or "").lower():
            return False
        subcategoria = filtros.get("subcategoria")
        if subcategoria and subcategoria.lower() not in (p.subcategoria or "").lower():
            return False
        marca = filtros.get("marca")
        if marca and marca.lower() not in (p.marca or "").lower():
            return False
        return True

    @staticmethod
    def _cumple_precio(p, filtros: dict) -> bool:
        precio = float(p.precio.monto)
        precio_min = filtros.get("precio_min")
        if precio_min is not None and precio < precio_min:
            return False
        precio_max = filtros.get("precio_max")
        if precio_max is not None and precio > precio_max:
            return False
        return True

    @classmethod
    def _cumple_pulgadas(cls, p, filtros: dict) -> bool:
        pulgadas = filtros.get("pulgadas")
        if pulgadas is not None and (p.pulgadas is None or abs(p.pulgadas - pulgadas) > cls._TOLERANCIA_PULGADAS):
            return False
        pulgadas_min = filtros.get("pulgadas_min")
        if pulgadas_min is not None and (p.pulgadas is None or p.pulgadas < pulgadas_min):
            return False
        pulgadas_max = filtros.get("pulgadas_max")
        if pulgadas_max is not None and (p.pulgadas is None or p.pulgadas > pulgadas_max):
            return False
        return True

    @classmethod
    def _cumple_minimos(cls, p, filtros: dict) -> bool:
        for campo, atributo in cls._MINIMOS:
            minimo = filtros.get(campo)
            if minimo is None:
                continue
            valor = getattr(p, atributo, None)
            if valor is None or valor < minimo:
                return False
        return True

    @staticmethod
    def _cumple_potencia_max(p, filtros: dict) -> bool:
        potencia_max = filtros.get("potencia_w_max")
        if potencia_max is None:
            return True
        return p.potencia_w is not None and p.potencia_w <= potencia_max

    @classmethod
    def _cumple_iguales(cls, p, filtros: dict) -> bool:
        for campo, atributo in cls._IGUALES:
            esperado = filtros.get(campo)
            if not esperado:
                continue
            actual = (getattr(p, atributo, None) or "").lower()
            if actual != esperado.lower():
                return False
        return True
