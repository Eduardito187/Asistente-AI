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
from .reranker_por_perfil import ReRankerPorPerfil
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

        query_base = BuscarProductosQuery(
            categoria=perfil.categoria_foco or None,
            subcategoria=perfil.subcategoria_foco or None,
            marca=None if marca_indiferente else (perfil.marca_preferida or None),
            precio_max=perfil.presupuesto_max,
            pulgadas=perfil.pulgadas,
            tipo_panel=perfil.tipo_panel,
            resolucion=perfil.resolucion,
            limite=12,
            excluir_accesorios=True,
        )
        if perfil.uso_declarado:
            from dataclasses import replace as _replace
            productos = self._buscar.ejecutar(_replace(query_base, query=perfil.uso_declarado))
            # Cuando el uso_declarado es poco frecuente en nombres (ej. "gaming" solo
            # aparece en 1 laptop), complementamos con una búsqueda amplia para
            # tener al menos 3 candidatos que el reranker pueda ordenar.
            if len(productos) < 3:
                extras = self._buscar.ejecutar(query_base)
                skus_vistos = {str(p.sku) for p in productos}
                productos = productos + [p for p in extras if str(p.sku) not in skus_vistos]
        else:
            productos = self._buscar.ejecutar(query_base)
        if not productos:
            return None

        # Ordena por calidad (panel/resolución/discount) como base, luego aplica
        # el reranker de perfil (uso_declarado, marca) para que productos que
        # matchean el uso declarado suban sobre accesorios con descuento.
        por_calidad = sorted(productos, key=self._score, reverse=True)
        rankeados = ReRankerPorPerfil().reordenar(
            por_calidad, perfil, marca_indiferente=marca_indiferente
        )
        principal = rankeados[0]
        alternativas = rankeados[1:3]

        lineas = [
            f"Con lo que me contas{self._resumen_contexto(perfil)}, te recomiendo:\n",
            "**Recomendación principal:**",
            f"- **{principal.nombre} — Bs {principal.precio.monto:.0f}** [{principal.sku}]",
            f"- Por qué conviene: {self._justificacion(principal)}",
        ]
        if alternativas:
            lineas.append("\n**Alternativas:**")
            etiquetas = self._etiquetar_alternativas(alternativas)
            for etiq, p in etiquetas:
                lineas.append(
                    f"- {etiq}: {p.nombre} — Bs {p.precio.monto:.0f} [{p.sku}]"
                    f" ({self._justificacion_corta(p)})"
                )
        lineas.append(self._conclusion(principal, alternativas))
        if perfil.uso_declarado:
            lineas.append("\nQuerés que lo agregamos al carrito o te cuento más de alguna?")
        else:
            lineas.append(
                "\n¿La necesitás para estudio, trabajo, diseño, programación o juegos? "
                "Así puedo ajustar mejor la recomendación."
            )

        elegidos = [principal, *alternativas]
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.detalle(p) for p in elegidos],
            skus=[str(p.sku) for p in elegidos],
            ruta="follow_up_recomendacion",
        )

    @staticmethod
    def _suficiente_contexto(perfil: ResultadoObtenerPerfilSesion) -> bool:
        tiene_que = bool(perfil.categoria_foco or perfil.pulgadas or perfil.uso_declarado)
        tiene_ancla = bool(
            perfil.presupuesto_max or perfil.pulgadas or perfil.tipo_panel or perfil.uso_declarado
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

    @staticmethod
    def _etiquetar_alternativas(
        alternativas: list[Producto],
    ) -> list[tuple[str, Producto]]:
        """Asigna etiqueta económica/intermedia/premium según precio relativo."""
        if not alternativas:
            return []
        ordenadas = sorted(alternativas, key=lambda p: p.precio.monto)
        if len(ordenadas) == 1:
            return [("Alternativa", ordenadas[0])]
        etiquetas = ["Opción económica", "Opción intermedia", "Opción premium"]
        if len(ordenadas) == 2:
            return [(etiquetas[0], ordenadas[0]), (etiquetas[2], ordenadas[1])]
        return list(zip(etiquetas, ordenadas))

    @staticmethod
    def _conclusion(principal: Producto, alternativas: list[Producto]) -> str:
        todos = sorted([principal, *alternativas], key=lambda p: p.precio.monto)
        barato = todos[0]
        caro = todos[-1]
        medio = principal
        lineas = ["\n**Conclusión:**"]
        if barato.sku != medio.sku:
            diff = medio.precio.monto - barato.precio.monto
            lineas.append(
                f"- Si buscás ahorrar, elegiría el **{barato.nombre}** — "
                f"cumple los requisitos clave a Bs {diff:.0f} menos que la opción principal."
            )
        lineas.append(
            f"- Si buscás la mejor relación calidad/precio, elegiría el **{medio.nombre}** — "
            f"es la recomendación principal por su balance de specs y precio."
        )
        if caro.sku != medio.sku:
            diff = caro.precio.monto - barato.precio.monto
            lineas.append(
                f"- Si querés mejor rendimiento, elegiría el **{caro.nombre}** — "
                f"mayor potencia, especialmente para tareas más exigentes "
                f"(Bs {diff:.0f} más que la opción económica)."
            )
        return "\n".join(lineas)

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
