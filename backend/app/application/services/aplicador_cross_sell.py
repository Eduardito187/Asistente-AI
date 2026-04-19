from __future__ import annotations

from ..chat.paso_agente import PasoAgente
from .sugeridor_cross_sell import SugeridorCrossSell


class AplicadorCrossSell:
    """SRP: leer el trace del turno, detectar agregar_al_carrito/confirmar_orden
    exitosos y anexar una linea de sugerencia (cross-sell) a la respuesta del
    asistente. No habla con LLM — es determinista."""

    def __init__(self, sugeridor: SugeridorCrossSell) -> None:
        self._sugeridor = sugeridor

    def aplicar(
        self,
        respuesta: str,
        trace: list[PasoAgente],
        productos: list[dict],
    ) -> str:
        if not self._disparo_compra(trace):
            return respuesta
        categoria = self._categoria_compra(trace, productos)
        skus_origen = {p.get("sku", "") for p in productos if p.get("sku")}
        sugerencias = self._sugeridor.sugerir(categoria, skus_origen)
        if not sugerencias:
            return respuesta
        return respuesta + "\n\n" + self._formatear(sugerencias)

    @staticmethod
    def _disparo_compra(trace: list[PasoAgente]) -> bool:
        return any(
            p.tool in ("agregar_al_carrito", "confirmar_orden") and not p.result.get("error")
            for p in trace
        )

    @staticmethod
    def _categoria_compra(trace: list[PasoAgente], productos: list[dict]) -> str | None:
        for p in productos:
            cat = p.get("categoria")
            if cat:
                return cat
        for paso in trace:
            if paso.tool == "ver_producto":
                cat = paso.result.get("categoria")
                if cat:
                    return cat
        return None

    @staticmethod
    def _formatear(sugerencias: list[dict]) -> str:
        lineas = ["Te puede interesar combinar con:"]
        for s in sugerencias:
            lineas.append(f"- [{s['sku']}] {s['nombre']} — Bs {s['precio_bob']:.0f}")
        return "\n".join(lineas)
