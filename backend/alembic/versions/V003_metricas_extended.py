"""V003 — Métricas turno: columnas de observabilidad y A/B testing.

Añade: prompt_version, quality_score, reason_code, variant_name,
busquedas_sin_resultado + índice asociado.

Revision ID: V003
Revises: V002
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "V003"
down_revision = "V002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        ALTER TABLE metricas_turno
            ADD COLUMN IF NOT EXISTS prompt_version          VARCHAR(40)  NULL,
            ADD COLUMN IF NOT EXISTS quality_score           TINYINT      NULL,
            ADD COLUMN IF NOT EXISTS reason_code             VARCHAR(40)  NULL,
            ADD COLUMN IF NOT EXISTS variant_name            VARCHAR(40)  NULL,
            ADD COLUMN IF NOT EXISTS busquedas_sin_resultado TINYINT(1)   NOT NULL DEFAULT 0
    """))
    op.execute(text("""
        ALTER TABLE metricas_turno
            ADD INDEX IF NOT EXISTS ix_sin_resultado (busquedas_sin_resultado, created_at)
    """))


def downgrade() -> None:
    op.execute(text("ALTER TABLE metricas_turno DROP INDEX IF EXISTS ix_sin_resultado"))
    op.execute(text("""
        ALTER TABLE metricas_turno
            DROP COLUMN IF EXISTS busquedas_sin_resultado,
            DROP COLUMN IF EXISTS variant_name,
            DROP COLUMN IF EXISTS reason_code,
            DROP COLUMN IF EXISTS quality_score,
            DROP COLUMN IF EXISTS prompt_version
    """))
