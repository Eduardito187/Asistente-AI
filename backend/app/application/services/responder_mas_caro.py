from __future__ import annotations

from uuid import UUID

from ..chat.serializers import ProductoSerializer
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
    ResultadoObtenerPerfilSesion,
)
from .respuesta_follow_up import RespuestaFollowUp


class ResponderMasCaro:
    """Short-circuit deterministico para 'algo mas premium / uno mejor'.

    Sube precio_min POR ENCIMA del precio_max_mostrado previo y prioriza
    panel premium (MINILED/QLED/OLED) + resolucion 4K/8K. Excluye SKUs ya
    mostrados."""

    _EPSILON = 1.0
    _PANELES_PREMIUM = ("MINILED", "QLED", "OLED")

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        buscar_productos: BuscarProductosHandler,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._buscar = buscar_productos

    def responder(self, sesion_id: UUID) -> RespuestaFollowUp | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        if not self._tiene_contexto(perfil):
            return None

        anchor = perfil.precio_max_mostrado
        if anchor is None:
            return None

        piso_nuevo = anchor + self._EPSILON
        excluidos = self._skus_mostrados(perfil)

        nuevos = self._buscar_premium(perfil, piso_nuevo, excluidos)
        if not nuevos:
            nuevos = self._buscar_cualquier_premium_por_precio(perfil, piso_nuevo, excluidos)

        if not nuevos:
            return RespuestaFollowUp(
                texto=(
                    f"En el catalogo no tengo algo mas premium que lo de Bs "
                    f"{anchor:.0f} dentro de los mismos filtros. Queres que "
                    "probemos relajando la categoria / pulgadas, o te muestro "
                    "la opcion mas top que tengo aunque sea similar?"
                ),
                ruta="follow_up_mas_caro_vacio",
            )

        lineas = [f"Subiendo la vara, estos son mas premium (desde Bs {piso_nuevo:.0f}):"]
        for p in nuevos:
            extra = (
                f" (antes Bs {p.precio_anterior.monto:.0f})"
                if p.precio_anterior else ""
            )
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        lineas.append("Cual queres que te arme?")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in nuevos],
            skus=[str(p.sku) for p in nuevos],
            ruta="follow_up_mas_caro",
        )

    def _buscar_premium(
        self,
        perfil: ResultadoObtenerPerfilSesion,
        piso: float,
        excluidos: set[str],
    ) -> list:
        for panel in self._PANELES_PREMIUM:
            productos = self._buscar.ejecutar(
                BuscarProductosQuery(
                    categoria=perfil.categoria_efectiva(),
                    subcategoria=perfil.subcategoria_efectiva(),
                    pulgadas=perfil.pulgadas,
                    tipo_panel=panel,
                    precio_min=piso,
                    limite=6,
                    excluir_accesorios=True,
                )
            )
            nuevos = [p for p in productos if str(p.sku) not in excluidos][:3]
            if nuevos:
                return nuevos
        return []

    def _buscar_cualquier_premium_por_precio(
        self,
        perfil: ResultadoObtenerPerfilSesion,
        piso: float,
        excluidos: set[str],
    ) -> list:
        productos = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=perfil.categoria_efectiva(),
                subcategoria=perfil.subcategoria_efectiva(),
                pulgadas=perfil.pulgadas,
                precio_min=piso,
                limite=6,
                excluir_accesorios=True,
            )
        )
        return [p for p in productos if str(p.sku) not in excluidos][:3]

    @staticmethod
    def _tiene_contexto(perfil: ResultadoObtenerPerfilSesion) -> bool:
        return bool(
            perfil.categoria_foco
            or perfil.pulgadas
            or perfil.alternativa_ofrecida
        )

    @staticmethod
    def _skus_mostrados(perfil: ResultadoObtenerPerfilSesion) -> set[str]:
        if not perfil.ultimos_skus_mostrados:
            return set()
        return {s for s in perfil.ultimos_skus_mostrados.split(",") if s}
