from __future__ import annotations


class PromptVariantsSql:
    LISTAR_ACTIVAS = (
        "SELECT id, variant_name, prompt_extra, weight, activa, descripcion, created_at "
        "FROM prompt_variants WHERE activa = 1 ORDER BY id ASC"
    )

    UPSERT = (
        "INSERT INTO prompt_variants (variant_name, prompt_extra, weight, activa, descripcion) "
        "VALUES (:name, :extra, :weight, :activa, :desc) "
        "ON DUPLICATE KEY UPDATE "
        "prompt_extra = VALUES(prompt_extra), weight = VALUES(weight), "
        "activa = VALUES(activa), descripcion = VALUES(descripcion)"
    )

    DESACTIVAR = "UPDATE prompt_variants SET activa = 0 WHERE variant_name = :name"
