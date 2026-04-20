from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RefinamientoShown:
    """VO inmutable con los atributos por los que el cliente pide refinar
    entre los productos ya mostrados ('cuales son electricas', 'solo los OLED')."""

    es_electrico: Optional[bool] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    color: Optional[str] = None

    def vacio(self) -> bool:
        return all(getattr(self, f) is None for f in self.__dataclass_fields__)

    def descripcion_humana(self) -> str:
        partes: list[str] = []
        if self.es_electrico is True:
            partes.append("electricos")
        if self.es_electrico is False:
            partes.append("a combustion")
        if self.tipo_panel:
            partes.append(f"panel {self.tipo_panel}")
        if self.resolucion:
            partes.append(self.resolucion)
        if self.color:
            partes.append(f"color {self.color}")
        return ", ".join(partes) or "esa caracteristica"
