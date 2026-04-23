from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from ..chat.serializers import ProductoSerializer
from ..chat.validador_filtros_duros import ValidadorFiltrosDuros
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
    ResultadoObtenerPerfilSesion,
)
from .refinamiento_shown import RefinamientoShown
from .respuesta_follow_up import RespuestaFollowUp


class ResponderRefinamientoShown:
    """Short-circuit para refinamientos sobre lo mostrado ('cuales son
    electricas', 'solo los OLED').

    Flujo:
      1. Toma los SKUs del turno previo desde el perfil.
      2. Los filtra por el atributo pedido (determinista, BD-driven).
      3. Si quedan, los responde como subconjunto.
      4. Si no queda ninguno, busca en catalogo con esa caracteristica dentro
         de la categoria activa y responde con honestidad ('de los que te
         mostre ninguno es X, pero tengo estos').
      5. Si tampoco hay, devuelve texto honesto sin lista."""

    _MAX = 3

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        comparar: CompararProductosHandler,
        buscar: BuscarProductosHandler,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._comparar = comparar
        self._buscar = buscar

    def responder(
        self, sesion_id: UUID, refinamiento: RefinamientoShown
    ) -> RespuestaFollowUp | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        skus = self._skus_mostrados(perfil)
        if not skus:
            return None

        productos_mostrados = self._cargar(skus)
        if not productos_mostrados:
            return None

        filtros = self._como_filtros(refinamiento)
        cumplen = [p for p in productos_mostrados if ValidadorFiltrosDuros.cumple(p, filtros)]
        if cumplen:
            return self._respuesta_subconjunto(cumplen, refinamiento)

        return self._respuesta_ampliada(perfil, refinamiento, productos_mostrados)

    @staticmethod
    def _skus_mostrados(perfil: ResultadoObtenerPerfilSesion) -> list[str]:
        if not perfil.ultimos_skus_mostrados:
            return []
        return [s for s in perfil.ultimos_skus_mostrados.split(",") if s]

    def _cargar(self, skus: list[str]):
        resultado = self._comparar.ejecutar(CompararProductosQuery(skus=tuple(skus)))
        return list(resultado.productos)

    @staticmethod
    def _como_filtros(r: RefinamientoShown) -> dict:
        return {k: v for k, v in asdict(r).items() if v is not None}

    def _respuesta_subconjunto(
        self, productos, refinamiento: RefinamientoShown
    ) -> RespuestaFollowUp:
        seleccion = productos[: self._MAX]
        lineas = [
            f"De las que te mostre, estas cumplen con {refinamiento.descripcion_humana()}:"
        ]
        for p in seleccion:
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f} [{p.sku}]")
        lineas.append("Alguna te convence o busco mas opciones?")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in seleccion],
            skus=[str(p.sku) for p in seleccion],
            ruta="follow_up_refinamiento_subconjunto",
        )

    def _respuesta_ampliada(
        self,
        perfil: ResultadoObtenerPerfilSesion,
        refinamiento: RefinamientoShown,
        productos_mostrados,
    ) -> RespuestaFollowUp:
        ampliados = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=perfil.categoria_efectiva(),
                subcategoria=perfil.subcategoria_efectiva(),
                marca=perfil.marca_preferida or None,
                precio_max=perfil.presupuesto_max,
                pulgadas=perfil.pulgadas,
                tipo_panel=refinamiento.tipo_panel or perfil.tipo_panel,
                resolucion=refinamiento.resolucion or perfil.resolucion,
                color=refinamiento.color,
                es_electrico=refinamiento.es_electrico,
                limite=6,
                excluir_accesorios=True,
            )
        )
        ya_mostrados = {str(p.sku) for p in productos_mostrados}
        nuevos = [p for p in ampliados if str(p.sku) not in ya_mostrados][: self._MAX]
        descripcion = refinamiento.descripcion_humana()
        if not nuevos:
            return RespuestaFollowUp(
                texto=(
                    f"De las que te mostre ninguna es {descripcion}, y no encuentro "
                    "otras asi en el catalogo con los mismos filtros. Queres que "
                    "probemos con otra marca o flexibilizamos algo?"
                ),
                ruta="follow_up_refinamiento_vacio",
            )
        lineas = [
            f"De las que te mostre ninguna es {descripcion}, pero encontre estas "
            "en el catalogo:"
        ]
        for p in nuevos:
            extra = (
                f" (antes Bs {p.precio_anterior.monto:.0f})"
                if p.precio_anterior else ""
            )
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        lineas.append("Alguna te sirve?")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in nuevos],
            skus=[str(p.sku) for p in nuevos],
            ruta="follow_up_refinamiento_ampliado",
        )
