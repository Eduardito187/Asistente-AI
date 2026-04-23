from __future__ import annotations

from uuid import UUID

from ..chat.serializers import ProductoSerializer
from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
)
from .renderizador_tabla_comparacion import RenderizadorTablaComparacion
from .respuesta_follow_up import RespuestaFollowUp


class ResponderComparacionMostrados:
    """Short-circuit para 'compara los anteriores / diferencias entre esos'.

    Toma los SKUs del turno previo desde el perfil y llama directo al
    handler de comparacion — evita que el LLM arranque busqueda nueva."""

    _MAX_SKUS = 4

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        comparar: CompararProductosHandler,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._comparar = comparar

    def responder(self, sesion_id: UUID) -> RespuestaFollowUp | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        if not perfil.ultimos_skus_mostrados:
            return None
        skus = [s for s in perfil.ultimos_skus_mostrados.split(",") if s][: self._MAX_SKUS]
        if len(skus) < 2:
            return None
        resultado = self._comparar.ejecutar(
            CompararProductosQuery(skus=tuple(skus))
        )
        productos = list(resultado.productos)
        if len(productos) < 2:
            return None

        texto = RenderizadorTablaComparacion.render(
            tabla=resultado.tabla,
            conclusion=resultado.conclusion,
            productos_por_sku={str(p.sku): p for p in productos},
            encabezado="Te los pongo lado a lado:",
        )
        if not texto:
            return None
        return RespuestaFollowUp(
            texto=texto,
            productos=[ProductoSerializer.detalle(p) for p in productos],
            skus=[str(p.sku) for p in productos],
            ruta="follow_up_comparacion",
        )
