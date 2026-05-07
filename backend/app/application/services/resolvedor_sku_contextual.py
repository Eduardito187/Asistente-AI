from __future__ import annotations

import re


class ResolvedorSkuContextual:
    """Resuelve el SKU al que se refiere el cliente cuando NO menciona uno
    explícitamente en el mensaje actual. Usa cascada de prioridades:

    1. `perfil.sku_foco` — el resolver de sinónimos lo identificó previamente
    2. Primer SKU de `perfil.ultimos_skus_mostrados` — el más reciente mostrado
    3. Primer SKU citado en el último mensaje del assistant del historial

    Útil para preguntas pronominales: 'sus características', 'más info',
    'cuéntame más', 'dame las specs' — el LLM Qwen 7B no resuelve bien
    pronombres entre turnos, así que lo hacemos determinístico."""

    # Captura SKUs en formato `[XYZ-123]` o `[ABC123]` del texto.
    # \w ya incluye [A-Za-z0-9_], así que solo agregamos los símbolos extra.
    _RX_SKU_EN_TEXTO = re.compile(
        r"\[([A-Za-zÑñ0-9][\w\-.#/()]{2,60})\]"
    )

    @classmethod
    def resolver(
        cls,
        perfil,
        historial_assistant: list[str] | None = None,
        historial_user: list[str] | None = None,
    ) -> str | None:
        """Devuelve el SKU candidato del contexto, o None si no hay ninguno
        razonable. Cascada de prioridades:

        1. perfil.sku_foco — explícitamente declarado
        2. perfil.ultimos_skus_mostrados — primero (más reciente)
        3. SKU citado por el assistant en su último mensaje
        4. SKU citado por el cliente en algún mensaje previo (fallback final
           para casos donde la persistencia falló)"""
        sku = cls._del_perfil_foco(perfil)
        if sku:
            return sku
        sku = cls._del_ultimos_mostrados(perfil)
        if sku:
            return sku
        sku = cls._del_historial(historial_assistant or [])
        if sku:
            return sku
        return cls._del_historial(historial_user or [])

    # ===== Internos ==========================================================

    @staticmethod
    def _del_perfil_foco(perfil) -> str | None:
        if perfil is None:
            return None
        sku = getattr(perfil, "sku_foco", None)
        return sku.strip() if isinstance(sku, str) and sku.strip() else None

    @staticmethod
    def _del_ultimos_mostrados(perfil) -> str | None:
        if perfil is None:
            return None
        skus_str = getattr(perfil, "ultimos_skus_mostrados", None)
        if not skus_str:
            return None
        # Si la sesión mostró 1 solo producto, ese es claramente "el del que habla".
        # Si mostró varios, devolvemos el primero (que en _persistir_turno_mostrado
        # se guarda en orden de presentación, primero = más relevante).
        skus = [s.strip() for s in skus_str.split(",") if s.strip()]
        return skus[0] if skus else None

    @classmethod
    def _del_historial(cls, historial: list[str]) -> str | None:
        """Busca SKUs en formato [XXX] del más reciente al más antiguo."""
        if not historial:
            return None
        for mensaje in reversed(historial):
            match = cls._RX_SKU_EN_TEXTO.search(mensaje or "")
            if match:
                return match.group(1)
        return None
