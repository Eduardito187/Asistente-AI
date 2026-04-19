from __future__ import annotations

from enum import Enum


class Intencion(str, Enum):
    """Clasificacion de intencion del turno del cliente.

    Solo las primeras tres (SALUDO, DESPEDIDA, GRACIAS) se pueden resolver
    sin llamar al LLM. El resto cae al agente con tool-calling.
    """

    SALUDO = "saludo"
    DESPEDIDA = "despedida"
    GRACIAS = "gracias"
    CONSULTA_PRODUCTO = "consulta_producto"
    ACCION_CARRITO = "accion_carrito"
    OTRO = "otro"
