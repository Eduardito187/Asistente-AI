from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TipoAtributo = Literal["int", "float", "bool", "str"]
OperadorSql  = Literal[">=", "=", "LIKE", "bool_text"]


@dataclass(frozen=True)
class DefinicionAtributo:
    """VO: describe un atributo filtrable de producto.

    Un registro por atributo = única fuente de verdad para:
    - si persiste en PerfilSesion (sticky)
    - cómo se mapea en SQL
    - qué parámetro usa en BuscarProductosQuery
    - qué texto ve el LLM en tool_definitions

    Para agregar un atributo nuevo: añadir una DefinicionAtributo al Catálogo.
    """

    nombre: str               # campo en BuscarProductosQuery / PerfilSesion
    tipo: TipoAtributo
    sticky: bool              # True = persiste entre turnos en PerfilSesion
    columna_sql: str          # columna o campo en tabla productos (puede ser vacío para bool_text)
    operador_sql: OperadorSql
    descripcion_llm: str      # descripción corta para tool_definitions
    ejemplo: str              # "120hz", "5000mah", "True"
