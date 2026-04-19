from __future__ import annotations

from ...domain.productos import Producto
from ..queries.obtener_perfil_sesion import ResultadoObtenerPerfilSesion
from .calculador_boost_comercial import CalculadorBoostComercial
from .calculador_boost_perfil import CalculadorBoostPerfil


class ReRankerPorPerfil:
    """SRP: reordenar productos combinando boost de perfil (lo que el cliente
    declaro) con boost comercial (calidad intrinseca del producto: panel premium,
    resolucion alta, smart TV, oferta activa)."""

    def reordenar(
        self,
        productos: list[Producto],
        perfil: ResultadoObtenerPerfilSesion,
        *,
        marca_indiferente: bool = False,
    ) -> list[Producto]:
        if not productos:
            return list(productos)
        scored = [
            (self._score_total(p, perfil, marca_indiferente), idx, p)
            for idx, p in enumerate(productos)
        ]
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [p for _s, _i, p in scored]

    @staticmethod
    def _score_total(
        producto: Producto,
        perfil: ResultadoObtenerPerfilSesion,
        marca_indiferente: bool,
    ) -> float:
        perfil_score = (
            0.0 if perfil.esta_vacio()
            else CalculadorBoostPerfil.score(producto, perfil, marca_indiferente=marca_indiferente)
        )
        return perfil_score + CalculadorBoostComercial.score(producto)
