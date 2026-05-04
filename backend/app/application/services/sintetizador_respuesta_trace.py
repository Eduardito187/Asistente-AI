from __future__ import annotations


class SintetizadorRespuestaTrace:
    """SRP: cuando el LLM no devuelve texto despues de tool-calling (max_iter
    consumido sin respuesta final), sintetizar una respuesta razonable a
    partir del ultimo buscar_productos del trace.

    Evita la respuesta canned 'se me complico resolver tu consulta' que es
    una mala experiencia. Aqui mostramos lo que ya tenemos."""

    @classmethod
    def sintetizar(cls, trace: list) -> str | None:
        if not trace:
            return None
        ultimo = cls._ultimo_buscar(trace)
        if ultimo is None:
            return None
        result = getattr(ultimo, "result", {}) or {}
        productos = result.get("productos") or []
        if not productos:
            return (
                "No encontre productos exactos para esa busqueda. "
                "Decime que tipo de producto buscas (laptop, celular, TV, "
                "freidora, etc.) y ajustamos juntos."
            )
        lineas = ["Encontre estas opciones en el catalogo:"]
        for p in productos[:3]:
            nombre = p.get("nombre", "Producto")
            precio = p.get("precio_bob") or p.get("precio") or 0
            sku = p.get("sku", "")
            lineas.append(f"- {nombre} — Bs {precio} [{sku}]")
        contradiccion = result.get("contradiccion_detectada")
        if contradiccion:
            lineas.append("")
            lineas.append(f"Atención: {contradiccion.get('explicacion', '')}")
        preguntas = result.get("preguntas_siguientes") or []
        if preguntas:
            lineas.append("")
            lineas.append(preguntas[0])
        return "\n".join(lineas)

    @staticmethod
    def _ultimo_buscar(trace: list):
        for paso in reversed(trace):
            if getattr(paso, "tool", None) == "buscar_productos":
                return paso
        return None
