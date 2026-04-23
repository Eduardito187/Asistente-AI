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


class ResponderMasBarato:
    """Short-circuit deterministico para 'alguna alternativa mas economica'.

    Reusa los filtros del perfil (categoria, pulgadas, panel, resolucion) y
    baja el precio_max por debajo del precio_min_mostrado del turno previo.
    Si no encuentra nada mas barato, responde honestamente sin listar lo
    mismo."""

    _EPSILON = 1.0

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

        anchor = perfil.precio_min_mostrado
        if anchor is None:
            return None

        techo_nuevo = max(anchor - self._EPSILON, anchor * 0.99)
        excluidos = self._skus_mostrados(perfil)

        productos = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=perfil.categoria_efectiva(),
                subcategoria=perfil.subcategoria_efectiva(),
                pulgadas=perfil.pulgadas,
                tipo_panel=perfil.tipo_panel,
                resolucion=perfil.resolucion,
                precio_max=techo_nuevo,
                limite=6,
                excluir_accesorios=True,
            )
        )
        nuevos = [p for p in productos if str(p.sku) not in excluidos][:3]

        if not nuevos:
            return RespuestaFollowUp(
                texto=(
                    f"Mire el catalogo y no encontre nada por debajo de Bs "
                    f"{anchor:.0f} con los mismos filtros ({self._resumen_filtros(perfil)}). "
                    "Queres que flexibilicemos alguno — bajar pulgadas, aceptar otra "
                    "marca, o cambiar panel?"
                ),
                ruta="follow_up_mas_barato_vacio",
            )

        lineas = [
            f"Te dejo opciones mas economicas (por debajo de Bs {anchor:.0f}):"
        ]
        for p in nuevos:
            extra = (
                f" (antes Bs {p.precio_anterior.monto:.0f})"
                if p.precio_anterior else ""
            )
            lineas.append(
                f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]"
            )
        lineas.append("Cual te late? Te la reservo.")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in nuevos],
            skus=[str(p.sku) for p in nuevos],
            ruta="follow_up_mas_barato",
        )

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

    @staticmethod
    def _resumen_filtros(perfil: ResultadoObtenerPerfilSesion) -> str:
        partes: list[str] = []
        if perfil.categoria_foco:
            partes.append(perfil.categoria_foco)
        if perfil.pulgadas:
            partes.append(f"{perfil.pulgadas:g}\"")
        if perfil.tipo_panel:
            partes.append(perfil.tipo_panel)
        if perfil.resolucion:
            partes.append(perfil.resolucion)
        return ", ".join(partes) or "los actuales"
