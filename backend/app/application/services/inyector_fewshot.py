from __future__ import annotations

from ..queries.obtener_ejemplos_fewshot import (
    ObtenerEjemplosFewShotHandler,
    ObtenerEjemplosFewShotQuery,
)


class InyectorFewShot:
    """SRP: construir el bloque de ejemplos few-shot a inyectar en el system
    prompt para que el modelo imite el tono y la concision comprobados."""

    LIMITE_DEFAULT = 3

    def __init__(self, ejemplos: ObtenerEjemplosFewShotHandler) -> None:
        self._ejemplos = ejemplos

    def bloque(self, limite: int | None = None) -> str:
        n = limite or self.LIMITE_DEFAULT
        conversaciones = self._ejemplos.ejecutar(ObtenerEjemplosFewShotQuery(limite=n))
        if not conversaciones:
            return ""
        partes = [
            "EJEMPLOS DE CONVERSACIONES QUE FUNCIONARON BIEN "
            "(imita el tono calido, corto y resolutivo; NO copies SKUs ni precios):",
        ]
        for i, c in enumerate(conversaciones, 1):
            cliente = self._recortar(c.cliente_texto, 400)
            asistente = self._recortar(c.asistente_texto, 600)
            partes.append(
                f"\nEjemplo {i}:\nCliente: {cliente}\nDismi: {asistente}"
            )
        return "\n".join(partes)

    @staticmethod
    def _recortar(texto: str, n: int) -> str:
        t = (texto or "").strip().replace("\n", " ")
        return t if len(t) <= n else t[:n] + "..."
