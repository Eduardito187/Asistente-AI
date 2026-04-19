from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoObtenerPerfilSesion:
    """DTO del perfil declarado de la sesion."""

    presupuesto_max: Optional[float]
    marca_preferida: Optional[str]
    categoria_foco: Optional[str]
    uso_declarado: Optional[str]
    pulgadas: Optional[float] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    ultimos_skus_mostrados: Optional[str] = None
    precio_min_mostrado: Optional[float] = None
    precio_max_mostrado: Optional[float] = None

    def esta_vacio(self) -> bool:
        return not any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.uso_declarado, self.pulgadas, self.tipo_panel, self.resolucion,
            ]
        )
