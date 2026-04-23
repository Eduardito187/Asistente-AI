from __future__ import annotations

from uuid import UUID

from ...domain.productos import SKU
from ..chat.serializers import ProductoSerializer
from ..ports import UnitOfWork
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
    ResultadoObtenerPerfilSesion,
)
from .respuesta_follow_up import RespuestaFollowUp
from .umbrales_tier import UmbralesTier


class ResponderOtraOpcion:
    """Short-circuit para 'otra opcion / alternativa'.

    Reusa los filtros del perfil sin tocar el rango de precio, pero EXCLUYE
    los SKUs del turno anterior. Si no hay mas, lo dice explicitamente en
    vez de repetir la lista."""

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        buscar_productos: BuscarProductosHandler,
        uow_factory,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._buscar = buscar_productos
        self._uow_factory = uow_factory

    def responder(self, sesion_id: UUID) -> RespuestaFollowUp | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        if not self._tiene_contexto(perfil):
            return None

        excluidos = self._skus_mostrados(perfil)
        piso, techo = self._rango_tier(perfil)
        productos = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=perfil.categoria_efectiva(),
                subcategoria=perfil.subcategoria_efectiva(),
                marca=perfil.marca_preferida or None,
                precio_min=piso,
                precio_max=self._techo(perfil.presupuesto_max, techo),
                pulgadas=perfil.pulgadas,
                tipo_panel=perfil.tipo_panel,
                resolucion=perfil.resolucion,
                limite=12,
                excluir_accesorios=True,
            )
        )
        nuevos = [p for p in productos if str(p.sku) not in excluidos][:3]
        if not nuevos and perfil.marca_preferida:
            productos_sin_marca = self._buscar.ejecutar(
                BuscarProductosQuery(
                    categoria=perfil.categoria_efectiva(),
                    subcategoria=perfil.subcategoria_efectiva(),
                    precio_max=perfil.presupuesto_max,
                    pulgadas=perfil.pulgadas,
                    tipo_panel=perfil.tipo_panel,
                    resolucion=perfil.resolucion,
                    limite=12,
                )
            )
            nuevos = [p for p in productos_sin_marca if str(p.sku) not in excluidos][:3]

        if not nuevos:
            return RespuestaFollowUp(
                texto=(
                    "Con esos filtros ya te mostre todo lo que tengo. Si "
                    "queres, probamos con otro tamanio, otra marca, o con "
                    "presupuesto distinto para ampliar el catalogo."
                ),
                ruta="follow_up_otra_opcion_vacio",
            )

        lineas = ["Va, otras opciones con los mismos filtros:"]
        for p in nuevos:
            extra = (
                f" (antes Bs {p.precio_anterior.monto:.0f})"
                if p.precio_anterior else ""
            )
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        lineas.append("Alguna te convence o seguimos mirando?")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in nuevos],
            skus=[str(p.sku) for p in nuevos],
            ruta="follow_up_otra_opcion",
        )

    def _rango_tier(
        self, perfil: ResultadoObtenerPerfilSesion
    ) -> tuple[float | None, float | None]:
        """Mantiene la gama del turno anterior: si el sku_foco es premium
        pero el cliente no lo declaró, inferimos el tier del precio del
        foco y filtramos low-end del siguiente listado."""
        subcat = perfil.subcategoria_efectiva()
        precio_foco = self._precio_foco(perfil.sku_foco)
        tier = perfil.desired_tier or (
            UmbralesTier.tier_de(precio_foco, subcat) if precio_foco else None
        )
        if not tier:
            return None, None
        return UmbralesTier.rango(
            tier=tier, subcategoria=subcat, precio_ancla=precio_foco
        )

    def _precio_foco(self, sku_foco: str | None) -> float | None:
        if not sku_foco:
            return None
        try:
            with self._uow_factory() as uow:
                prod = uow.productos.obtener_por_sku(SKU(sku_foco))
        except Exception:
            return None
        return float(prod.precio.monto) if prod else None

    @staticmethod
    def _techo(presupuesto: float | None, techo_tier: float | None) -> float | None:
        if presupuesto is None:
            return techo_tier
        if techo_tier is None:
            return presupuesto
        return min(presupuesto, techo_tier)

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
