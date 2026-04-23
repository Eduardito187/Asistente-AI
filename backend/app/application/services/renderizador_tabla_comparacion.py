from __future__ import annotations


class RenderizadorTablaComparacion:
    """SRP: construye el markdown de una comparación (tabla + 3 bullets) a
    partir del resultado estructurado de `comparar_productos`. Se usa:

      - en el short-circuit de comparación explícita (sin LLM)
      - como post-processor cuando el LLM invocó comparar_productos, para
        reemplazar la tabla que el LLM improvisó por una generada por código
        (evita alucinaciones de specs).

    Único motivo de cambio: el layout de salida de la comparación.
    """

    _ETIQUETAS = (
        ("mejor_general", "Mejor opción general"),
        ("mejor_precio_calidad", "Mejor relación precio/calidad"),
        ("mas_economica", "Opción más económica"),
    )

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
        header = ["**Atributo**", *(f"**{n}**" for n in nombres)]
        lineas.append("| " + " | ".join(header) + " |")
        lineas.append("| " + " | ".join(["---"] * (len(nombres) + 1)) + " |")
        for fila in filas:
            campo = fila.get("campo", "")
            valores = [str(v) for v in fila.get("valores", [])]
            lineas.append(f"| {campo} | " + " | ".join(valores) + " |")
        lineas.append("")
        for clave, etiqueta in cls._ETIQUETAS:
            bloque = (conclusion or {}).get(clave) or {}
            sku = bloque.get("sku")
            razon = bloque.get("razon", "")
            nombre = cls._nombre(por_sku, sku, bloque, tabla)
            if sku and nombre:
                lineas.append(f"- **{etiqueta}:** {nombre} [{sku}] — {razon}")
        return "\n".join(lineas)

    @staticmethod
    def _nombre(
        por_sku: dict[str, object], sku: str | None, bloque: dict, tabla: dict
    ) -> str | None:
        """Resuelve el nombre por tres vias en orden: diccionario producto,
        campo `nombre` del bloque conclusion, o mapear sku→nombre en la tabla
        via posicion (tabla.skus alineado con tabla.nombres)."""
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
