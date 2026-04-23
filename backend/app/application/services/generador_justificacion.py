from __future__ import annotations

from ...domain.productos import Producto
from ..queries.obtener_perfil_sesion import ResultadoObtenerPerfilSesion
from .calculador_boost_perfil import PALABRAS_CLAVE_USO

MAX_FRASES = 2


class GeneradorJustificacion:
    """SRP: producir una frase corta explicando por que el producto encaja con el perfil."""

    @classmethod
    def para(cls, producto: Producto, perfil: ResultadoObtenerPerfilSesion) -> str | None:
        """Devuelve una frase corta que argumenta el producto. Si el perfil esta
        vacio, cae a senales del producto (descuento, oferta) para que el
        mensaje no quede frio. Prioriza: descuento > marca > uso > presupuesto.
        """
        partes: list[str] = []
        frase = cls._frase_descuento(producto)
        if frase:
            partes.append(frase)
        if not perfil.esta_vacio():
            frase = cls._frase_marca(producto, perfil.marca_preferida)
            if frase:
                partes.append(frase)
            frase = cls._frase_uso(producto, perfil.uso_declarado)
            if frase:
                partes.append(frase)
            frase = cls._frase_presupuesto(producto, perfil.presupuesto_max)
            if frase:
                partes.append(frase)
        if not partes:
            return None
        return " · ".join(partes[:MAX_FRASES])

    @staticmethod
    def _frase_descuento(p: Producto) -> str | None:
        """Si hay rebaja significativa (>=10%), destacala — es palanca comercial
        fuerte y el cliente lo valora aunque el perfil este vacio."""
        if not p.precio_anterior or p.precio_anterior.monto <= p.precio.monto:
            return None
        ahorro = p.precio_anterior.monto - p.precio.monto
        pct = ahorro / p.precio_anterior.monto * 100
        if pct < 10:
            return None
        return f"{pct:.0f}% off (ahorrás Bs {ahorro:.0f})"

    @staticmethod
    def _frase_marca(p: Producto, marca_pref: str | None) -> str | None:
        if not marca_pref or not p.marca:
            return None
        if marca_pref.lower() == p.marca.lower():
            return f"tu marca preferida ({p.marca})"
        return None

    @staticmethod
    def _frase_uso(p: Producto, uso: str | None) -> str | None:
        if not uso:
            return None
        claves = PALABRAS_CLAVE_USO.get(uso.lower(), ())
        if not claves:
            return None
        texto = f"{p.nombre} {p.descripcion or ''}".lower()
        if any(k in texto for k in claves):
            return f"encaja con uso {uso}"
        return None

    @staticmethod
    def _frase_presupuesto(p: Producto, presupuesto: float | None) -> str | None:
        if not presupuesto:
            return None
        if p.precio.monto <= presupuesto:
            margen = presupuesto - p.precio.monto
            if margen >= 500:
                return "te queda margen de presupuesto"
            return "entra en tu presupuesto"
        return None
