from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FormatoSolicitado:
    """VO con la directiva de formato pedida explicitamente por el cliente
    en este turno ("dame solo comprar/evitar", "en una frase", "maximo 3").

    Tres dimensiones independientes:
    - `forma`: shape preset (ej. 'comprar_evitar', 'seguro_barato'). Define
      labels y orden de las lineas que el LLM debe usar.
    - `max_productos`: tope de productos a citar. None = sin tope explicito.
    - `max_frases`: tope global de oraciones en la respuesta. None = sin
      tope. 1 fuerza respuesta de una sola frase por seccion.

    Cualquier campo None significa "no impuesto por el cliente"."""

    forma: Optional[str] = None
    max_productos: Optional[int] = None
    max_frases: Optional[int] = None

    def vacio(self) -> bool:
        return self.forma is None and self.max_productos is None and self.max_frases is None
