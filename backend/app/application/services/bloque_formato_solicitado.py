from __future__ import annotations

from .formato_solicitado import FormatoSolicitado


class BloqueFormatoSolicitado:
    """SRP: traduce un `FormatoSolicitado` al texto que se inyecta en el
    contexto del turno del LLM. Todo el rendering de directivas vive aqui
    para que `procesar_chat_service` solo decida cuando aplicarlo."""

    @classmethod
    def renderizar(cls, fmt: FormatoSolicitado) -> str | None:
        if fmt.vacio():
            return None
        bloques: list[str] = []
        forma = cls._render_forma(fmt.forma)
        if forma:
            bloques.append(forma)
        if fmt.max_productos is not None:
            bloques.append(
                f"Maximo {fmt.max_productos} producto(s) citado(s) en total. "
                "No agregues mas opciones que ese tope."
            )
        if fmt.max_frases is not None and fmt.max_frases <= 2:
            bloques.append(
                f"Cada seccion en MAXIMO {fmt.max_frases} oracion(es). "
                "Si necesitas mas detalle, pone N/D y deja que el cliente lo pregunte."
            )
        bloques.append(
            "NO incluyas preguntas de cierre genericas tipo "
            "'contame que te importa mas'. NO repreguntes datos ya en el perfil."
        )
        return "FORMATO ESTE TURNO (cliente lo pidio explicitamente):\n" + "\n".join(
            f"- {b}" for b in bloques
        )

    @staticmethod
    def _render_forma(forma: str | None) -> str | None:
        if forma == "comprar_evitar":
            return (
                "Estructura EXACTA con 3 lineas (sin encabezados, sin tabla):\n"
                "  Comprar: <Nombre — Bs precio [SKU]> — <razon en una frase>\n"
                "  Evitar: <que NO comprar y por que> — <razon breve>\n"
                "  Por que: <una frase sintetizando lo clave>"
            )
        if forma == "seguro_barato":
            return (
                "Estructura EXACTA con 2 lineas (sin encabezados):\n"
                "  Segura: <Nombre — Bs precio [SKU]> — <por que es la apuesta segura>\n"
                "  Barata: <Nombre — Bs precio [SKU]> — <por que es la mas accesible>"
            )
        return None
