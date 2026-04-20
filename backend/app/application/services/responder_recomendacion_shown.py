from __future__ import annotations

from uuid import UUID

from ...domain.productos import Producto
from ..chat.serializers import ProductoSerializer
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
    ResultadoObtenerPerfilSesion,
)
from .respuesta_follow_up import RespuestaFollowUp


class ResponderRecomendacionShown:
    """Short-circuit para 'cual me conviene / asesorame'.

    A diferencia del LLM generico, NO devuelve una lista plana: elige UNA
    recomendacion principal + 1-2 alternativas + una razon concreta. Usa
    scoring tecnico (panel OLED > QLED > MINILED > LED; 4K > FHD) y
    value-score (spec/precio) para seleccionar la principal.

    Requiere que ya haya datos de contexto (categoria o pulgadas) y que
    el perfil tenga, por lo menos, presupuesto o tamanio declarado. Si no,
    devuelve None para que el LLM haga las preguntas de perfilado."""

    _PANEL_SCORE = {"OLED": 4, "QLED": 3, "MINILED": 3, "NANOCELL": 2, "LED": 1}
    _RESO_SCORE = {"8K": 4, "4K": 3, "FHD": 2, "HD": 1}

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        buscar_productos: BuscarProductosHandler,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._buscar = buscar_productos

    def responder(
        self, sesion_id: UUID, marca_indiferente: bool
    ) -> RespuestaFollowUp | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        if not self._suficiente_contexto(perfil):
            return None

        productos = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=perfil.categoria_foco or None,
                marca=None if marca_indiferente else (perfil.marca_preferida or None),
                precio_max=perfil.presupuesto_max,
                pulgadas=perfil.pulgadas,
                tipo_panel=perfil.tipo_panel,
                resolucion=perfil.resolucion,
                limite=12,
            )
        )
        if not productos:
            return None

        rankeados = sorted(productos, key=self._score, reverse=True)
        principal = rankeados[0]
        alternativas = rankeados[1:3]

        lineas = [
            f"Con lo que me contas{self._resumen_contexto(perfil)}, te recomiendo:",
            f"**1) {principal.nombre} — Bs {principal.precio.monto:.0f}** [{principal.sku}]",
            f"   Por que: {self._justificacion(principal)}",
        ]
        if alternativas:
            lineas.append("Alternativas:")
            for p in alternativas:
                lineas.append(
                    f"- {p.nombre} — Bs {p.precio.monto:.0f} [{p.sku}] "
                    f"({self._justificacion_corta(p)})"
                )
        lineas.append("Queres que armemos la principal o te cuento mas de alguna?")

        elegidos = [principal, *alternativas]
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in elegidos],
            skus=[str(p.sku) for p in elegidos],
            ruta="follow_up_recomendacion",
        )

    @staticmethod
    def _suficiente_contexto(perfil: ResultadoObtenerPerfilSesion) -> bool:
        tiene_que = bool(perfil.categoria_foco or perfil.pulgadas)
        tiene_ancla = bool(
            perfil.presupuesto_max or perfil.pulgadas or perfil.tipo_panel
        )
        return tiene_que and tiene_ancla

    @classmethod
    def _score(cls, p: Producto) -> tuple[float, float, float, float]:
        panel = cls._PANEL_SCORE.get((p.tipo_panel or "").upper(), 0)
        reso = cls._RESO_SCORE.get((p.resolucion or "").upper(), 0)
        value = (panel + reso) / max(p.precio.monto / 1000.0, 0.1)
        descuento = 0.0
        if p.precio_anterior and p.precio_anterior.monto > p.precio.monto:
            descuento = (p.precio_anterior.monto - p.precio.monto) / p.precio_anterior.monto
        return (panel, reso, value, descuento)

    @classmethod
    def _justificacion(cls, p: Producto) -> str:
        partes: list[str] = []
        panel_up = (p.tipo_panel or "").upper()
        if panel_up in ("OLED", "QLED", "MINILED"):
            partes.append(f"panel {panel_up} (tope de gama)")
        elif panel_up:
            partes.append(f"panel {panel_up}")
        if (p.resolucion or "").upper() in ("4K", "8K"):
            partes.append(p.resolucion)
        if p.pulgadas:
            partes.append(f"{p.pulgadas:g}\"")
        if p.precio_anterior and p.precio_anterior.monto > p.precio.monto:
            ahorro = p.precio_anterior.monto - p.precio.monto
            partes.append(f"ahorras Bs {ahorro:.0f} respecto al precio anterior")
        if not partes:
            partes.append("mejor ratio ficha tecnica / precio del catalogo")
        return ", ".join(partes)

    @classmethod
    def _justificacion_corta(cls, p: Producto) -> str:
        panel_up = (p.tipo_panel or "").upper()
        if panel_up in ("OLED", "QLED", "MINILED"):
            return f"panel {panel_up}"
        if p.precio_anterior and p.precio_anterior.monto > p.precio.monto:
            return "con descuento"
        if p.resolucion:
            return p.resolucion
        return "opcion mas economica"

    @staticmethod
    def _resumen_contexto(perfil: ResultadoObtenerPerfilSesion) -> str:
        partes: list[str] = []
        if perfil.pulgadas:
            partes.append(f"{perfil.pulgadas:g}\"")
        if perfil.presupuesto_max:
            partes.append(f"hasta Bs {perfil.presupuesto_max:.0f}")
        if perfil.categoria_foco:
            partes.append(perfil.categoria_foco)
        if not partes:
            return ""
        return " (" + ", ".join(partes) + ")"
