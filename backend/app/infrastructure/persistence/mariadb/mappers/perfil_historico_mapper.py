from __future__ import annotations

import json

from .....domain.perfiles_historicos import PerfilHistorico


class PerfilHistoricoMapper:
    """Materializa un PerfilHistorico desde un row crudo."""

    @staticmethod
    def from_row(r: dict) -> PerfilHistorico:
        snap = r.get("perfil_snapshot")
        if isinstance(snap, str):
            try:
                snap = json.loads(snap)
            except (TypeError, ValueError):
                snap = {}
        return PerfilHistorico(
            id=r["id"],
            contacto_hash=r["contacto_hash"],
            perfil_snapshot=snap or {},
            ultima_categoria=r.get("ultima_categoria"),
            ultima_marca=r.get("ultima_marca"),
            ultima_compra_sku=r.get("ultima_compra_sku"),
            visitas=int(r.get("visitas") or 1),
            primera_vez=r["primera_vez"],
            ultima_vez=r["ultima_vez"],
        )
