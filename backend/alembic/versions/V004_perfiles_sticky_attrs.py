"""V004 — Perfiles sesión: atributos técnicos sticky (Fase 1).

Agrega todas las columnas de atributos filtrables que deben persistir
entre turnos de conversación para no pedir al cliente que los repita:
refresh_hz_min, bateria_mah_min, camara_mp_min, soporta_5g,
sistema_operativo, capacidad_kg_min, potencia_w_min, inverter,
no_frost, smart_tv, bluetooth_incluido, nfc, usb_c, hdmi_2_1.

Regla de merge (aplicada en ActualizarPerfilSesionHandler):
  - Booleanos: guardar True/NULL — nunca False explícito.
  - Numéricos:  COALESCE(nuevo, viejo) — el último valor gana.

Revision ID: V004
Revises: V003
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "V004"
down_revision = "V003"
branch_labels = None
depends_on = None

_NUEVAS_COLUMNAS = """
    ADD COLUMN IF NOT EXISTS refresh_hz_min     SMALLINT     NULL COMMENT 'Hz mínimos de refresco de pantalla (120, 144, 165, 240)',
    ADD COLUMN IF NOT EXISTS bateria_mah_min    INT          NULL COMMENT 'mAh mínimos de batería (celulares/tablets)',
    ADD COLUMN IF NOT EXISTS camara_mp_min      SMALLINT     NULL COMMENT 'Megapíxeles mínimos de cámara principal',
    ADD COLUMN IF NOT EXISTS soporta_5g         TINYINT(1)   NULL COMMENT '1=requiere 5G; NULL=indiferente',
    ADD COLUMN IF NOT EXISTS sistema_operativo  VARCHAR(30)  NULL COMMENT 'android|windows|ios|linux',
    ADD COLUMN IF NOT EXISTS capacidad_kg_min   DECIMAL(5,1) NULL COMMENT 'Carga mínima en kg (lavadoras)',
    ADD COLUMN IF NOT EXISTS potencia_w_min     INT          NULL COMMENT 'Vatios mínimos (electrodomésticos)',
    ADD COLUMN IF NOT EXISTS inverter           TINYINT(1)   NULL COMMENT '1=requiere tecnología inverter',
    ADD COLUMN IF NOT EXISTS no_frost           TINYINT(1)   NULL COMMENT '1=requiere no-frost (refrigeradoras)',
    ADD COLUMN IF NOT EXISTS smart_tv           TINYINT(1)   NULL COMMENT '1=requiere smart TV',
    ADD COLUMN IF NOT EXISTS bluetooth_incluido TINYINT(1)   NULL COMMENT '1=requiere Bluetooth',
    ADD COLUMN IF NOT EXISTS nfc               TINYINT(1)   NULL COMMENT '1=requiere NFC',
    ADD COLUMN IF NOT EXISTS usb_c             TINYINT(1)   NULL COMMENT '1=requiere USB-C',
    ADD COLUMN IF NOT EXISTS hdmi_2_1          TINYINT(1)   NULL COMMENT '1=requiere HDMI 2.1'
"""

_COLUMNAS_A_ELIMINAR = [
    "refresh_hz_min", "bateria_mah_min", "camara_mp_min", "soporta_5g",
    "sistema_operativo", "capacidad_kg_min", "potencia_w_min", "inverter",
    "no_frost", "smart_tv", "bluetooth_incluido", "nfc", "usb_c", "hdmi_2_1",
]


def upgrade() -> None:
    op.execute(text(f"ALTER TABLE perfiles_sesion {_NUEVAS_COLUMNAS}"))


def downgrade() -> None:
    drops = ", ".join(f"DROP COLUMN IF EXISTS {c}" for c in _COLUMNAS_A_ELIMINAR)
    op.execute(text(f"ALTER TABLE perfiles_sesion {drops}"))
