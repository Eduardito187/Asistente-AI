from __future__ import annotations

import re
from uuid import UUID

from ..chat.tool_dispatcher import ToolDispatcher
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
)
from .respuesta_follow_up import RespuestaFollowUp


class AtajoOrdinalCarrito:
    """SRP: resolver pedidos tipo 'agrega el primero al carrito' / 'quiero el
    segundo' / 'llevame el tercero' usando el orden de productos mostrados
    en el turno previo. Sin LLM: lee ultimos_skus_mostrados del perfil,
    llama agregar_al_carrito via dispatcher y devuelve la confirmacion."""

    _ORDINALES = (
        ("primero", 0), ("primera", 0), ("1ro", 0), ("1ro.", 0), ("1.", 0),
        ("segundo", 1), ("segunda", 1), ("2do", 1), ("2do.", 1), ("2.", 1),
        ("tercero", 2), ("tercera", 2), ("3ro", 2), ("3ro.", 2), ("3.", 2),
    )
    _RX_VERBO = re.compile(
        r"\b(agrega|agrégame|agregame|quiero|llevame|llevate|me\s+llevo|"
        r"suma|pon|poneme|dame|reserva)\b",
        re.IGNORECASE,
    )
    _RX_ORDINAL = re.compile(
        r"\b(el|la|al)\s+(primer[oa]?|segund[oa]|tercer[oa]|"
        r"1ro\.?|2do\.?|3ro\.?|1\.|2\.|3\.)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        dispatcher: ToolDispatcher,
        obtener_perfil: ObtenerPerfilSesionHandler,
    ) -> None:
        self._dispatcher = dispatcher
        self._obtener_perfil = obtener_perfil

    def resolver(self, mensaje: str, sesion_id: UUID) -> RespuestaFollowUp | None:
        if not self._RX_VERBO.search(mensaje or ""):
            return None
        idx = self._indice_ordinal(mensaje)
        if idx is None:
            return None
        sku = self._sku_por_indice(sesion_id, idx)
        if sku is None:
            return None
        resultado = self._dispatcher.ejecutar(
            "agregar_al_carrito", {"sku": sku}, sesion_id
        )
        if resultado.get("error"):
            return None
        texto = (
            f"Listo, agregue [{sku}] al carrito. "
            "Queres seguir viendo mas opciones o cerramos la compra?"
        )
        return RespuestaFollowUp(
            texto=texto,
            productos=[],
            skus=[sku],
            ruta="atajo_ordinal_carrito",
        )

    @classmethod
    def _indice_ordinal(cls, mensaje: str) -> int | None:
        texto = (mensaje or "").lower()
        if not cls._RX_ORDINAL.search(texto):
            return None
        for palabra, idx in cls._ORDINALES:
            if re.search(rf"\b{re.escape(palabra)}\b", texto):
                return idx
        return None

    def _sku_por_indice(self, sesion_id: UUID, idx: int) -> str | None:
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        csv = perfil.ultimos_skus_mostrados or ""
        skus = [s for s in csv.split(",") if s]
        if idx >= len(skus):
            return None
        return skus[idx]
