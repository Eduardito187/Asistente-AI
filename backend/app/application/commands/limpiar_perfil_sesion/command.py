from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LimpiarPerfilSesionCommand:
    """Limpia campos de búsqueda del perfil (categoria, marca, SKU, uso, specs).
    Preserva: presupuesto_max, presupuesto_ideal, ciudad_sesion, genero_declarado,
    frustracion_count — son atributos del usuario, no del contexto de búsqueda."""

    sesion_id: UUID
