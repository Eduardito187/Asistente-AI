from __future__ import annotations


class GeneradorCierreContextual:
    """SRP: produce la oracion de cierre que sigue a la lista de productos
    en el path forzado de busqueda. Adapta el cierre al estado del perfil
    para NO repetir preguntas que el cliente ya respondio.

    Reglas (regla 7 del system_prompt + feedback usuario):
    - Si el perfil ya tiene presupuesto + (marca o uso) + algun hard req
      (ram_gb_min, gpu_dedicada, ssd_gb_min): el cliente ya nos dio TODO,
      cerramos con un resumen y preguntamos si quiere ajustar UNA cosa.
    - Si falta solo `uso` y todo lo demas esta lleno: pregunta puntual
      sobre uso (mas util que el cierre generico).
    - Si falta marca + presupuesto + uso: cierre generico (estado actual).
    - Avisos de fallback (gpu_*, marca_*) ganan sobre la heuristica del
      perfil — esos cierres son parte del mensaje honesto del fallback."""

    @classmethod
    def generar(cls, aviso_fallback: str | None, perfil) -> str:
        cierre_aviso = cls._cierre_por_aviso(aviso_fallback)
        if cierre_aviso is not None:
            return cierre_aviso
        if perfil is None:
            return cls._CIERRE_GENERICO
        if cls._cliente_dio_suficiente_contexto(perfil):
            resumen = cls._resumen_filtros(perfil)
            if resumen:
                return (
                    f"Con lo que me dijiste estoy priorizando {resumen}. "
                    "Te sirve alguna de estas o ajustamos algo?"
                )
            return "Te sirve alguna de estas o queres que ajuste algo?"
        # Cierre dinamico: lista solo los slots que el cliente NO declaro.
        faltantes = cls._slots_faltantes(perfil)
        if faltantes:
            resumen = cls._resumen_filtros(perfil)
            prefijo = (
                f"Ya tengo {resumen}. " if resumen else ""
            )
            return (
                f"{prefijo}Para afinar la recomendacion, contame "
                f"{cls._pregunta_por_faltantes(faltantes)}."
            )
        return cls._CIERRE_GENERICO

    _CIERRE_GENERICO = (
        "Contame que te importa mas (presupuesto, marca, uso) y te ayudo a elegir."
    )

    @classmethod
    def _slots_faltantes(cls, perfil) -> list[str]:
        """Lista los slots conversacionales que el cliente NO declaro y serian
        utiles para afinar. Orden de prioridad: presupuesto > uso > marca."""
        salida: list[str] = []
        if not getattr(perfil, "presupuesto_max", None):
            salida.append("presupuesto")
        if not getattr(perfil, "uso_declarado", None):
            salida.append("uso")
        if not getattr(perfil, "marca_preferida", None):
            salida.append("marca")
        return salida

    @staticmethod
    def _pregunta_por_faltantes(faltantes: list[str]) -> str:
        """Genera la frase humana para preguntar SOLO los slots faltantes
        en orden de prioridad. No incluye los ya declarados."""
        if len(faltantes) == 1:
            mapa = {
                "presupuesto": "tu presupuesto aproximado",
                "uso": "para que la vas a usar (estudio/gaming/diseño/oficina)",
                "marca": "si tenes alguna marca preferida",
            }
            return mapa[faltantes[0]]
        # 2 o 3 slots: lista compacta humana.
        return f"que te importa mas ({', '.join(faltantes)})"

    @staticmethod
    def _cierre_por_aviso(aviso_fallback: str | None) -> str | None:
        if aviso_fallback == "gpu_dedicada_no_confirmada":
            return (
                "Estas opciones no tienen GPU dedicada confirmada — pueden servir para "
                "oficina y estudio pero no para render o CAD serio. "
                "Queres que busque algo especifico o ajustamos el presupuesto?"
            )
        if aviso_fallback and aviso_fallback.startswith("gpu_sobre_presupuesto:"):
            presupuesto = aviso_fallback.split(":", 1)[1]
            return (
                f"Estan sobre tu presupuesto de Bs {presupuesto}, pero son las unicas "
                f"con GPU confirmada en catalogo. Vale la pena la diferencia para render/CAD?"
            )
        if aviso_fallback and aviso_fallback.startswith("marca_no_encontrada:"):
            return "Son alternativas de otras marcas — si queres ajustar la busqueda, avisame."
        return None

    @staticmethod
    def _cliente_dio_suficiente_contexto(perfil) -> bool:
        """True cuando el cliente declaro presupuesto + (marca o uso) + algun
        hard req tecnico. Repreguntar slots seria friccion innecesaria."""
        tiene_presupuesto = bool(getattr(perfil, "presupuesto_max", None))
        tiene_marca = bool(getattr(perfil, "marca_preferida", None))
        tiene_uso = bool(getattr(perfil, "uso_declarado", None))
        tiene_hard_req = any(
            getattr(perfil, attr, None)
            for attr in ("ram_gb_min", "ssd_gb_min", "gpu_dedicada", "pulgadas")
        )
        return tiene_presupuesto and (tiene_marca or tiene_uso) and tiene_hard_req

    @staticmethod
    def _solo_falta_uso(perfil) -> bool:
        tiene_presupuesto = bool(getattr(perfil, "presupuesto_max", None))
        tiene_uso = bool(getattr(perfil, "uso_declarado", None))
        tiene_hard_req = any(
            getattr(perfil, attr, None)
            for attr in ("ram_gb_min", "ssd_gb_min", "gpu_dedicada", "pulgadas")
        )
        return tiene_presupuesto and tiene_hard_req and not tiene_uso

    @staticmethod
    def _resumen_filtros(perfil) -> str:
        """Resume los filtros declarados en frase humana corta."""
        partes: list[str] = []
        uso = getattr(perfil, "uso_declarado", None)
        if uso:
            partes.append(str(uso).strip().lower())
        cat = getattr(perfil, "categoria_foco", None)
        if cat:
            partes.append(str(cat).strip().lower())
        ram = getattr(perfil, "ram_gb_min", None)
        if ram:
            partes.append(f"{ram}GB de RAM")
        ssd = getattr(perfil, "ssd_gb_min", None)
        if ssd:
            partes.append(f"SSD {ssd}GB")
        if getattr(perfil, "gpu_dedicada", None):
            partes.append("GPU dedicada")
        marca = getattr(perfil, "marca_preferida", None)
        if marca:
            partes.append(f"marca {marca}")
        presupuesto = getattr(perfil, "presupuesto_max", None)
        if presupuesto:
            partes.append(f"hasta Bs {int(presupuesto)}")
        return ", ".join(partes)
