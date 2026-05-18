"""V005 — notas_usuario en perfiles_sesion.

Campo de texto libre donde se acumulan las instrucciones de memoria
del cliente: "recuerda que...", "no olvides que...", etc.
Formato: líneas separadas por \\n, máx. 2000 caracteres.

Revision ID: V005
Revises: V004
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "V005"
down_revision = "V004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text(
        "ALTER TABLE perfiles_sesion "
        "ADD COLUMN IF NOT EXISTS notas_usuario TEXT NULL "
        "COMMENT 'Hechos que el cliente pidio recordar: recuerda que...'"
    ))


def downgrade() -> None:
    op.execute(text(
        "ALTER TABLE perfiles_sesion DROP COLUMN IF EXISTS notas_usuario"
    ))
