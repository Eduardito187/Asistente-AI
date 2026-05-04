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
    alternativa_ofrecida: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    genero_declarado: Optional[str] = None
    sku_foco: Optional[str] = None
    desired_tier: Optional[str] = None
    ram_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None
    ssd_gb_min: Optional[int] = None
    nombre_excluye_acum: Optional[str] = None  # comma-separated
    presupuesto_ideal: Optional[float] = None  # techo blando preferido del cliente

    def esta_vacio(self) -> bool:
        return not any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.subcategoria_foco, self.uso_declarado, self.pulgadas,
                self.tipo_panel, self.resolucion, self.alternativa_ofrecida,
            ]
        )

    def categoria_efectiva(self) -> Optional[str]:
        """Categoria activa para follow-ups: si el usuario no declaro
        categoria_foco pero el agente le ofrecio una alternativa en el turno
        anterior (ej. 'Celulares/Smartphones' tras pedir 'xiaomi 17 pro max'),
        esa alternativa ES la categoria activa para 'otra opcion'/'mas barato'."""
        if self.categoria_foco:
            return self.categoria_foco
        if self.alternativa_ofrecida:
            return self.alternativa_ofrecida.split("/", 1)[0]
        return None

    def subcategoria_efectiva(self) -> Optional[str]:
        if self.subcategoria_foco:
            return self.subcategoria_foco
        if self.alternativa_ofrecida and "/" in self.alternativa_ofrecida:
            return self.alternativa_ofrecida.split("/", 1)[1]
        return None

    def exclusiones_acumuladas(self) -> list[str]:
        """Retorna la lista deduplicada de exclusiones acumuladas."""
        if not self.nombre_excluye_acum:
            return []
        return list(dict.fromkeys(
            kw.strip() for kw in self.nombre_excluye_acum.split(",") if kw.strip()
        ))
