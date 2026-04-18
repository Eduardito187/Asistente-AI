from __future__ import annotations

from typing import Optional


class CarritoReadSql:
    """Catalogo SQL del read-model de carritos (vista_carritos)."""

    _SELECT_BASE = (
        "SELECT sesion_id, estado, cliente_nombre, cliente_email, "
        "cliente_telefono, items, total_bob, ultima_actividad_at "
        "FROM vista_carritos"
    )

    @classmethod
    def listar(cls, estado: Optional[str], solo_con_items: bool) -> tuple[str, dict]:
        clauses: list[str] = []
        params: dict = {}
        if estado:
            clauses.append("estado = :estado")
            params["estado"] = estado
        if solo_con_items:
            clauses.append("items > 0")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"{cls._SELECT_BASE} {where} ORDER BY ultima_actividad_at DESC LIMIT :l"
        return sql, params
