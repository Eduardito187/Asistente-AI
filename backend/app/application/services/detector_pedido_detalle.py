from __future__ import annotations

import re

RX_PEDIDO_DETALLE = re.compile(
    r"\b(detalle|detalles|cuentame|contame|cuenta mas|mas info|mas informacion|"
    r"describe|descripcion|especificac|caracteristic|ventaja|beneficio|"
    r"comparar|comparacion|diferencia|por que|porque conviene|sirve para|"
    r"pantalla|procesador|memoria|bateria|camara|resolucion|peso|teclado|"
    r"conectividad|puerto|puertos|sistema operativo|gpu|grafica|ram|ssd)\b",
    re.IGNORECASE,
)


class DetectorPedidoDetalle:
    """SRP: decidir si el mensaje del cliente es un pedido de informacion
    detallada/descriptiva sobre un producto. Usado para ajustar el flujo
    del agente (atajo rapido vs respuesta rica con specs)."""

    @classmethod
    def es_pedido_detalle(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        return bool(RX_PEDIDO_DETALLE.search(mensaje))
