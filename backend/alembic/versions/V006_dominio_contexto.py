"""V006 – dominio_contexto: guarda snapshot de attrs por dominio para switching dinámico.

Revision ID: V006
Revises: V005
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa

revision = "V006"
down_revision = "V005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE perfiles_sesion "
        "ADD COLUMN IF NOT EXISTS dominio_contexto TEXT NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE perfiles_sesion "
        "DROP COLUMN IF EXISTS dominio_contexto"
    )
