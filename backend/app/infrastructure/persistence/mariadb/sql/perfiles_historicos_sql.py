from __future__ import annotations


class PerfilesHistoricosSql:
    """Catalogo SQL del agregado PerfilHistorico."""

    UPSERT = (
        "INSERT INTO perfiles_historicos "
        "(contacto_hash, perfil_snapshot, ultima_categoria, ultima_marca, ultima_compra_sku) "
        "VALUES (:hash, :snap, :cat, :marca, :sku) "
        "ON DUPLICATE KEY UPDATE "
        "perfil_snapshot = VALUES(perfil_snapshot), "
        "ultima_categoria = COALESCE(VALUES(ultima_categoria), ultima_categoria), "
        "ultima_marca = COALESCE(VALUES(ultima_marca), ultima_marca), "
        "ultima_compra_sku = COALESCE(VALUES(ultima_compra_sku), ultima_compra_sku), "
        "visitas = visitas + 1, "
        "ultima_vez = CURRENT_TIMESTAMP"
    )

    POR_HASH = (
        "SELECT id, contacto_hash, perfil_snapshot, ultima_categoria, "
        "ultima_marca, ultima_compra_sku, visitas, primera_vez, ultima_vez "
        "FROM perfiles_historicos WHERE contacto_hash = :hash"
    )
