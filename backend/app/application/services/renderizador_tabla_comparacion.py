from __future__ import annotations


class RenderizadorTablaComparacion:
    """SRP: construye el markdown de una comparación (tabla + ganador por
    criterio + recomendación final) a partir del resultado estructurado de
    `comparar_productos`. Se usa:

      - en el short-circuit de comparación explícita (sin LLM)
      - como post-processor cuando el LLM invocó comparar_productos, para
        reemplazar la tabla que el LLM improvisó por una generada por código
        (evita alucinaciones de specs).

    Único motivo de cambio: el layout de salida de la comparación.
    """

    _ETIQUETAS_GANADOR = (
        ("mejor_general",       "Mejor rendimiento"),
        ("mejor_precio_calidad", "Mejor calidad/precio"),
        ("mas_economica",        "Mejor precio"),
    )

    _ND = "N/D"

    @classmethod
    def render(
        cls,
        tabla: dict | None,
        conclusion: dict | None,
        productos_por_sku: dict[str, object] | None = None,
        encabezado: str = "Te comparo los que mencionaste:",
    ) -> str:
        tabla = tabla or {}
        nombres = tabla.get("nombres") or []
        filas = tabla.get("filas") or []
        if not nombres or not filas:
            return ""
        por_sku = productos_por_sku or {}
        lineas = [encabezado + "\n"]
        lineas.extend(cls._tabla_markdown(nombres, filas))
        lineas.append("")
        lineas.extend(cls._seccion_ganadores(conclusion, por_sku, tabla))
        lineas.extend(cls._seccion_recomendacion_final(conclusion, por_sku, tabla))
        return "\n".join(lineas)

    @classmethod
    def _tabla_markdown(cls, nombres: list, filas: list) -> list[str]:
        header = ["**Atributo**", *(f"**{n}**" for n in nombres)]
        sep = ["---"] * (len(nombres) + 1)
        lineas = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(sep) + " |",
        ]
        for fila in filas:
            campo = fila.get("campo", "")
            valores = cls._normalizar_valores(fila.get("valores", []), len(nombres))
            lineas.append(f"| {campo} | " + " | ".join(valores) + " |")
        return lineas

    @classmethod
    def _normalizar_valores(cls, raw: list, ncols: int) -> list[str]:
        resultado = [str(v) if v not in (None, "", "null") else cls._ND for v in raw]
        while len(resultado) < ncols:
            resultado.append(cls._ND)
        return resultado

    @classmethod
    def _seccion_ganadores(
        cls, conclusion: dict | None, por_sku: dict, tabla: dict
    ) -> list[str]:
        ganadores = []
        for clave, etiqueta in cls._ETIQUETAS_GANADOR:
            bloque = (conclusion or {}).get(clave) or {}
            sku = bloque.get("sku")
            nombre = cls._nombre(por_sku, sku, bloque, tabla)
            if sku and nombre:
                razon = bloque.get("razon", "")
                ganadores.append(f"- **{etiqueta}:** {nombre} — {razon}")
        if not ganadores:
            return []
        return ["**Ganador por criterio:**", *ganadores, ""]

    @classmethod
    def _seccion_recomendacion_final(
        cls, conclusion: dict | None, por_sku: dict, tabla: dict
    ) -> list[str]:
        mejor = (conclusion or {}).get("mejor_general") or {}
        sku_rec = mejor.get("sku")
        nombre_rec = cls._nombre(por_sku, sku_rec, mejor, tabla)
        if not sku_rec or not nombre_rec:
            return []
        razon_rec = mejor.get("razon", "")
        return [f"**Recomendación final:** {nombre_rec} [{sku_rec}] — {razon_rec}"]

    @staticmethod
    def _nombre(
        por_sku: dict[str, object], sku: str | None, bloque: dict, tabla: dict
    ) -> str | None:
        if not sku:
            return None
        prod = por_sku.get(sku)
        if prod is not None and hasattr(prod, "nombre"):
            return prod.nombre
        if bloque.get("nombre"):
            return bloque["nombre"]
        skus = tabla.get("skus") or []
        nombres = tabla.get("nombres") or []
        if sku in skus:
            idx = skus.index(sku)
            if idx < len(nombres):
                return nombres[idx]
        return None
