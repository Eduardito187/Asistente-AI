from __future__ import annotations

import re


class VerificadorAvanceTurno:
    """Post-LLM. Evalúa si el turno aportó valor o fue circular.

    AVANCE = el turno hizo algo concreto:
    - Tool transaccional exitosa (agregar/quitar/confirmar/comparar)
    - Búsqueda con ≥1 SKU NUEVO citado en la respuesta
    - Respuesta corta con dato concreto (precio, spec con número, SKU)

    SIN AVANCE = el LLM contestó pero no movió la conversación:
    - No hubo tool exitosa este turno
    - No citó SKUs nuevos respecto a turnos anteriores
    - Respuesta vaga sin números/SKUs/datos concretos

    Se usa para (1) métrica de calidad conversacional, (2) en futuro,
    flagear turnos sin avance al LLM en el siguiente turno para que
    cambie de estrategia."""

    _TOOLS_DE_AVANCE = frozenset({
        "buscar_productos", "comparar_productos", "ver_producto",
        "agregar_al_carrito", "quitar_del_carrito", "confirmar_orden",
        "vaciar_carrito",
    })

    _RX_PRECIO = re.compile(r"\bbs\.?\s*\d", re.IGNORECASE)
    _RX_SKU_TAG = re.compile(r"\[[A-Za-zÑñ0-9][\w\-.#_/()]{2,}\]")
    _RX_NUM_CON_UNIDAD = re.compile(
        r"\b\d+\s*(?:gb|tb|mp|hz|w|watts?|pulgadas?|inch|kg|"
        r"litros?|mah|años?|meses?)\b",
        re.IGNORECASE,
    )

    @classmethod
    def hubo_avance(
        cls,
        respuesta: str,
        skus_citados_actuales: list[str],
        skus_historicos_mostrados: list[str],
        trace: list,
    ) -> bool:
        if cls._tool_de_avance_exitosa(trace):
            return True
        if cls._cito_sku_nuevo(skus_citados_actuales, skus_historicos_mostrados):
            return True
        return cls._tiene_dato_concreto(respuesta)

    @classmethod
    def _tool_de_avance_exitosa(cls, trace: list) -> bool:
        for paso in trace:
            tool = getattr(paso, "tool", None)
            result = getattr(paso, "result", None) or {}
            if tool in cls._TOOLS_DE_AVANCE and not result.get("error"):
                return True
        return False

    @staticmethod
    def _cito_sku_nuevo(actuales: list[str], historicos: list[str]) -> bool:
        if not actuales:
            return False
        vistos = {str(s) for s in (historicos or [])}
        return any(str(s) not in vistos for s in actuales)

    @classmethod
    def _tiene_dato_concreto(cls, respuesta: str) -> bool:
        if not respuesta:
            return False
        if cls._RX_PRECIO.search(respuesta):
            return True
        if cls._RX_SKU_TAG.search(respuesta):
            return True
        return bool(cls._RX_NUM_CON_UNIDAD.search(respuesta))
