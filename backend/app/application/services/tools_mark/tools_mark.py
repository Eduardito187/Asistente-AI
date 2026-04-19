from __future__ import annotations

from ...chat.paso_agente import PasoAgente


class ToolsMark:
    """Marca de metadata de tools embebida al final del mensaje del asistente."""

    OPEN = "<!--TOOLS\n"
    CLOSE = "\n-->"

    @classmethod
    def strip(cls, texto: str) -> str:
        """Remueve el bloque de metadata de herramientas del final del texto."""
        i = texto.find(cls.OPEN)
        return texto[:i].rstrip() if i >= 0 else texto

    @classmethod
    def wrap(cls, respuesta: str, resumen: str) -> str:
        """Anexa la marca al respuesta si hay resumen, sino devuelve tal cual."""
        if not resumen:
            return respuesta
        return f"{respuesta}\n\n{cls.OPEN}{resumen}{cls.CLOSE}"

    @staticmethod
    def resumir(trace: list[PasoAgente]) -> str:
        """Serializa el trace de tools en un resumen corto para el historial."""
        if not trace:
            return ""
        skus_info: dict[str, str] = {}
        cart_snapshot: dict | None = None
        for p in trace:
            r = p.result or {}
            if p.tool == "buscar_productos":
                for prod in r.get("productos", []):
                    skus_info[prod["sku"]] = (
                        f"{prod['nombre']} Bs{prod['precio_bob']}"
                    )
            elif p.tool == "ver_producto" and "sku" in r:
                skus_info[r["sku"]] = f"{r.get('nombre','')} Bs{r.get('precio_bob','')}"
            elif p.tool == "ver_carrito":
                cart_snapshot = r

        partes: list[str] = []
        if skus_info:
            listado = "; ".join(f"{sku}={desc}" for sku, desc in skus_info.items())
            partes.append(f"SKUs vistos en este turno: {listado}")
        if cart_snapshot:
            items = cart_snapshot.get("items", [])
            if items:
                detalle = ", ".join(f"{i['sku']}x{i['cantidad']}" for i in items)
                partes.append(
                    f"Carrito actual: {detalle} total Bs{cart_snapshot.get('total_bob', 0)}"
                )
            else:
                partes.append("Carrito actual: vacio")
        return "\n".join(partes)
