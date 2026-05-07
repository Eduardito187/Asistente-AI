from __future__ import annotations


class DetectorLoopTool:
    """Detecta cuando el LLM se está estancando en un patrón nocivo de
    tool calls dentro del mismo turno y devuelve un mensaje correctivo
    para inyectar al loop, forzándolo a cambiar de estrategia.

    Patrones detectados:
    1. `ver_producto` 2+ veces con error de SKU no encontrado → el LLM
       está alucinando SKUs. Lo redirigimos a `buscar_productos`.
    2. `buscar_productos` 2+ veces con `total: 0` → la query no matchea
       nada. Le pedimos relajar filtros o usar palabras simples.
    3. `listar_categorias` 2+ veces seguidas sin progreso → el LLM está
       eludiendo `buscar_productos`. Lo forzamos a buscar.
    4. Cualquier tool 3+ veces con args idénticos → loop infinito.

    SRP: solo evaluar el trace acumulado y devolver el mensaje correctivo
    si aplica. Quien inyecta es el caller (AgenteService)."""

    _UMBRAL_VER_PRODUCTO_ERROR = 2
    _UMBRAL_BUSCAR_VACIO = 2
    # Listar_categorias raramente es útil — el LLM lo usa para "explorar" pero
    # nunca aporta SKUs comprables. Disparamos correctivo desde la PRIMERA
    # llamada para forzar buscar_productos rápidamente. Reduce 1 iteración
    # del loop = ~10-15s menos de latencia bajo concurrencia.
    _UMBRAL_LISTAR_CATEGORIAS = 1
    _UMBRAL_REPETICION_IDENTICA = 3

    @classmethod
    def correctivo(cls, trace: list, paso_actual_tool: str, paso_actual_result: dict) -> str | None:
        """Si el último paso (ya añadido al trace) cierra un patrón nocivo,
        devuelve un texto correctivo para reemplazar el resultado tool que
        ve el LLM. None si todo va bien."""
        # Repetición idéntica gana por encima de los otros patrones (loop muerto).
        repeticion = cls._correctivo_repeticion_identica(trace)
        if repeticion:
            return repeticion
        if paso_actual_tool == "ver_producto":
            return cls._correctivo_ver_producto(trace, paso_actual_result)
        if paso_actual_tool == "buscar_productos":
            return cls._correctivo_buscar_vacio(trace, paso_actual_result)
        if paso_actual_tool == "listar_categorias":
            return cls._correctivo_listar_categorias(trace)
        return None

    @classmethod
    def _correctivo_ver_producto(cls, trace: list, result: dict) -> str | None:
        if "error" not in (result or {}):
            return None
        # Cuenta cuántas veces ver_producto cerró con error en este turno.
        errores = sum(
            1 for p in trace
            if getattr(p, "tool", None) == "ver_producto"
            and "error" in (getattr(p, "result", None) or {})
        )
        if errores < cls._UMBRAL_VER_PRODUCTO_ERROR:
            return None
        skus_intentados = sorted({
            (getattr(p, "args", None) or {}).get("sku", "")
            for p in trace
            if getattr(p, "tool", None) == "ver_producto"
        } - {""})
        return (
            f"STOP: ya intentaste ver_producto {errores} veces con SKUs que "
            f"NO EXISTEN ({', '.join(skus_intentados[:3])}). "
            "Estás alucinando SKUs — los SKUs reales solo aparecen como "
            "respuesta de buscar_productos, NUNCA los inventes. "
            "ACCION OBLIGATORIA: llamá buscar_productos con query='laptop' "
            "(u otra palabra simple del producto pedido) en lugar de "
            "ver_producto. Si después la búsqueda devuelve productos, "
            "podes citarlos con [SKU]."
        )

    @classmethod
    def _correctivo_listar_categorias(cls, trace: list) -> str | None:
        """Si el LLM llama listar_categorias 2+ veces seguidas en el mismo
        turno, está eludiendo buscar_productos. Lo forzamos."""
        ultimas = [getattr(p, "tool", None) for p in trace[-cls._UMBRAL_LISTAR_CATEGORIAS:]]
        if len(ultimas) < cls._UMBRAL_LISTAR_CATEGORIAS:
            return None
        if not all(t == "listar_categorias" for t in ultimas):
            return None
        return (
            f"STOP: ya llamaste listar_categorias {len(ultimas)} veces. "
            "Eso NO ayuda al cliente — listar_categorias es solo un índice "
            "interno, no devuelve productos comprables. "
            "ACCION OBLIGATORIA: extraé del último mensaje del cliente UNA "
            "palabra de producto (ej. 'laptop', 'celular', 'TV') y llamá "
            "buscar_productos(query='<esa palabra>'). Si el cliente dijo "
            "'laptop para ingeniería civil', usá query='laptop'. Si dijo "
            "'algo para mi cocina', preguntale CUAL producto exactamente."
        )

    @classmethod
    def _correctivo_repeticion_identica(cls, trace: list) -> str | None:
        """Si la misma tool con los mismos args aparece >= 3 veces en el
        trace, el LLM está en un loop infinito. Forzamos respuesta de texto."""
        if len(trace) < cls._UMBRAL_REPETICION_IDENTICA:
            return None
        ultimos = trace[-cls._UMBRAL_REPETICION_IDENTICA:]
        firmas = {(getattr(p, "tool", None), str(getattr(p, "args", None) or {})) for p in ultimos}
        if len(firmas) > 1:
            return None
        nombre = getattr(ultimos[-1], "tool", "?")
        return (
            f"STOP: llamaste {nombre} con args idénticos {cls._UMBRAL_REPETICION_IDENTICA} "
            "veces seguidas. Estás en un loop infinito. "
            "DEJA DE LLAMAR TOOLS AHORA. Respondé al cliente con texto "
            "directo: pedile más contexto en una sola pregunta concreta o "
            "decile honestamente que no podés ayudarlo con esa información."
        )

    @classmethod
    def _correctivo_buscar_vacio(cls, trace: list, result: dict) -> str | None:
        if (result or {}).get("total", 1) != 0:
            return None
        vacios = sum(
            1 for p in trace
            if getattr(p, "tool", None) == "buscar_productos"
            and (getattr(p, "result", None) or {}).get("total", 1) == 0
        )
        if vacios < cls._UMBRAL_BUSCAR_VACIO:
            return None
        return (
            f"STOP: buscar_productos devolvió 0 resultados {vacios} veces. "
            "Tus filtros son demasiado restrictivos o el query es muy verbose. "
            "ACCION OBLIGATORIA: relajá filtros (quitá precio_max, marca, "
            "atributos boolean) y usá `query` con UNA palabra simple del "
            "producto: 'laptop', 'celular', 'freidora'. Si seguís sin "
            "resultados, respondé al cliente con 'No tengo ese producto en "
            "catálogo' — NO sigas reintentando con variaciones."
        )
