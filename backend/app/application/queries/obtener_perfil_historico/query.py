from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObtenerPerfilHistoricoQuery:
    """Busca snapshot de PerfilSesion previo del cliente por hash de contacto."""

    contacto_hash: str
