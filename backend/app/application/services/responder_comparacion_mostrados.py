from __future__ import annotations

from uuid import UUID

from ..chat.serializers import ProductoSerializer
from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
)
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

        lineas = ["Te los pongo lado a lado:"]
        for p in productos:
            lineas.append(
                f"- [{p.sku}] {p.nombre}: "
                f"{self._atributos_clave(p)} · Bs {p.precio.monto:.0f}"
            )
        lineas.append(
            "En resumen: el mas barato es "
            f"[{self._mas_barato(productos)}]; el de mejor ficha tecnica es "
            f"[{self._mejor_ficha(productos)}]. Cual te cierra?"
        )
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in productos],
            skus=[str(p.sku) for p in productos],
            ruta="follow_up_comparacion",
        )

    @staticmethod
    def _atributos_clave(p) -> str:
        partes: list[str] = []
        if p.pulgadas:
            partes.append(f"{p.pulgadas:g}\"")
        if p.tipo_panel:
            partes.append(p.tipo_panel)
        if p.resolucion:
            partes.append(p.resolucion)
        if p.marca:
            partes.append(p.marca)
        return " · ".join(partes) or "sin specs registradas"

    @staticmethod
    def _mas_barato(productos) -> str:
        return str(min(productos, key=lambda p: p.precio.monto).sku)

    @staticmethod
    def _mejor_ficha(productos):
        ranking_panel = {"OLED": 4, "QLED": 3, "MINILED": 3, "LED": 1, "NANOCELL": 2}
        ranking_reso = {"8K": 4, "4K": 3, "FHD": 2, "HD": 1}

        def puntaje(p) -> tuple[int, int, float]:
            return (
                ranking_panel.get((p.tipo_panel or "").upper(), 0),
                ranking_reso.get((p.resolucion or "").upper(), 0),
                p.precio.monto,
            )

        return str(max(productos, key=puntaje).sku)
