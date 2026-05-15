from __future__ import annotations

from .detector_marca_mensaje import DetectorMarcaMensaje


class AnunciadorFallbackMarca:
    """Post-procesador determinista: cuando el cliente solicitó una marca
    específica pero los productos devueltos son de otra marca, antepone el
    aviso obligatorio antes que el LLM lo omita.

    Condición de activación:
      - El mensaje del usuario menciona una marca conocida.
      - Ningún producto en la lista pertenece a esa marca.
      - La respuesta NO contiene ya la frase de aviso (evita duplicados).

    Solo actúa si hay ≥ 1 producto devuelto (si no hay productos, el
    ManejadorProductoAusente ya se encarga del mensaje).
    """

    _PREFIJO_AVISO = "No hay stock de {marca}, te muestro alternativas:\n\n"
    _SENALES_AVISO = (
        "no hay stock de", "no encontre", "no encontramos", "no tenemos",
        "no encontre stock", "no hay ", "sin stock", "no disponible",
    )

    @classmethod
    def aplicar(
        cls,
        respuesta: str,
        mensaje_usuario: str,
        productos: list[dict],
    ) -> str:
        if not productos:
            return respuesta
        marca_solicitada = DetectorMarcaMensaje.extraer(mensaje_usuario)
        if not marca_solicitada:
            return respuesta
        resp_lower = respuesta.lower()
        for senal in cls._SENALES_AVISO:
            if senal in resp_lower:
                return respuesta
        if cls._productos_tienen_marca(productos, marca_solicitada):
            return respuesta
        aviso = cls._PREFIJO_AVISO.format(marca=marca_solicitada.upper())
        return aviso + respuesta

    @staticmethod
    def _productos_tienen_marca(productos: list[dict], marca: str) -> bool:
        marca_lower = marca.lower()
        for p in productos:
            nombre = (p.get("nombre") or "").lower()
            marca_prod = (p.get("marca") or "").lower()
            if marca_lower in nombre or marca_lower in marca_prod:
                return True
        return False
