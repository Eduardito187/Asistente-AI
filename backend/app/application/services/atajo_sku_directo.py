from __future__ import annotations

from uuid import UUID

from ..chat.tool_dispatcher import ToolDispatcher
from .detector_pedido_detalle import DetectorPedidoDetalle
from .detector_sku_mensaje import DetectorSkuMensaje
from .respuesta_sku_directa import RespuestaSkuDirecta


class AtajoSkuDirecto:
    """SRP: resolver consultas tipo "quiero el producto ACE-NHU1PAA001"
    sin pasar por el loop LLM. Si el mensaje contiene un SKU que existe
    en catalogo, arma la respuesta con ficha + precio + stock.

    Si el cliente ademas pide detalles/descripcion, cede el turno al LLM
    para que genere una respuesta mas rica con la ficha completa.
    """

    def __init__(self, detector: DetectorSkuMensaje, dispatcher: ToolDispatcher) -> None:
        self._detector = detector
        self._dispatcher = dispatcher

    _MENSAJE_TIENDA_FISICA = (
        "Este producto ya no está disponible para compra online. "
        "Para adquirirlo debés acercarte a una tienda física Dismac."
    )

    def resolver(self, mensaje: str, sesion_id: UUID) -> RespuestaSkuDirecta | None:
        if DetectorPedidoDetalle.es_pedido_detalle(mensaje):
            return None
        ficha = self.ficha_si_existe(mensaje, sesion_id)
        if ficha is None:
            return None
        if ficha.get("solo_tienda_fisica") or ficha.get("es_descontinuado"):
            return RespuestaSkuDirecta(
                sku=str(ficha.get("sku") or ""),
                texto=self._MENSAJE_TIENDA_FISICA,
                producto=None,
            )
        return RespuestaSkuDirecta(
            sku=str(ficha.get("sku") or ""),
            texto=self._formatear(ficha),
            producto=ficha,
        )

    def ficha_si_existe(self, mensaje: str, sesion_id: UUID) -> dict | None:
        """Busca un SKU en el mensaje y devuelve la ficha si existe. Util para
        pre-enriquecer el contexto del agente cuando el cliente pide detalles.
        """
        sku = self._detector.extraer(mensaje)
        if not sku:
            return None
        resultado = self._dispatcher.ejecutar("ver_producto", {"sku": sku}, sesion_id)
        if resultado.get("error"):
            return None
        return resultado

    @staticmethod
    def _formatear(p: dict) -> str:
        nombre = p.get("nombre") or ""
        precio = p.get("precio_bob") or 0
        precio_ant = p.get("precio_anterior_bob")
        marca = p.get("marca") or ""
        partes = [f"Encontre {nombre}"]
        if marca:
            partes.append(f"de {marca}")
        extra_precio = (
            f"a Bs {precio:.0f} (antes Bs {precio_ant:.0f})"
            if precio_ant
            else f"a Bs {precio:.0f}"
        )
        partes.append(f"{extra_precio} [{p.get('sku')}]")
        return f"{' '.join(partes)}. Te cuento las specs o preferis que te compare con alternativas cercanas?"
