from __future__ import annotations

from ...domain.productos import Producto
from ..queries.obtener_perfil_sesion import ResultadoObtenerPerfilSesion
from .calculador_boost_comercial import CalculadorBoostComercial
from .calculador_boost_perfil import CalculadorBoostPerfil
from .calculador_boost_uso_tecnico import CalculadorBoostUsoTecnico


class ReRankerPorPerfil:
    """SRP: reordenar productos combinando boost de perfil (lo que el cliente
    declaro), boost comercial (calidad intrinseca: panel premium, oferta) y
    boost-de-uso-tecnico (specs reales ponderadas segun uso_declarado)."""

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
        if perfil.esta_vacio():
            perfil_score = 0.0
            uso_score = 0.0
        else:
            perfil_score = CalculadorBoostPerfil.score(
                producto, perfil, marca_indiferente=marca_indiferente,
            )
            uso_score = CalculadorBoostUsoTecnico.score(producto, perfil)
        return perfil_score + uso_score + CalculadorBoostComercial.score(producto)
