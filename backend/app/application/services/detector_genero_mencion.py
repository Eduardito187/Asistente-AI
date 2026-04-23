from __future__ import annotations

import re
from typing import Optional

from ...domain.shared.normalizacion import NormalizadorTexto


class DetectorGeneroMencion:
    """SRP: detecta si el cliente esta pidiendo un producto dirigido a un genero
    especifico ("para mujer", "de caballero", "para niño"). Devuelve el valor
    del ENUM `productos.genero` o None si el mensaje no indica nada.

    Ejemplos:
      'tienen un reloj para mujer?'    -> 'femenino'
      'relojes de caballero'            -> 'masculino'
      'algo para mi hijo'               -> 'infantil'
      'un smart watch'                  -> None
    """

    _RX_FEMENINO = re.compile(
        r"\b(mujer|mujeres|femenino|femenina|femeninas|dama|damas|"
        r"para mujer|de mujer|de dama|para dama|para mi esposa|para mi novia|"
        r"para mi hija|para mi mama)\b",
        re.IGNORECASE,
    )
    _RX_MASCULINO = re.compile(
        r"\b(hombre|hombres|caballero|caballeros|varon|varones|"
        r"masculino|masculina|masculinas|"
        r"para hombre|de hombre|para caballero|de caballero|"
        r"para mi esposo|para mi novio|para mi hijo|para mi papa|para mi padre)\b",
        re.IGNORECASE,
    )
    _RX_INFANTIL = re.compile(
        r"\b(nino|ninio|nina|ninia|bebe|bebes|infantil|"
        r"para nino|para nina|para bebe|"
        r"para mi hijo|para mi hija)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, texto: str | None) -> Optional[str]:
        if not texto:
            return None
        t = NormalizadorTexto.normalizar(texto)
        if cls._RX_INFANTIL.search(t):
            return "infantil"
        if cls._RX_FEMENINO.search(t):
            return "femenino"
        if cls._RX_MASCULINO.search(t):
            return "masculino"
        return None
