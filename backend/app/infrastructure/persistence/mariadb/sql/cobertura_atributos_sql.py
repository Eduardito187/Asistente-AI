from __future__ import annotations


class CoberturaAtributosSql:
    """SQL para estadísticas de cobertura de columnas estructuradas en productos."""

    COBERTURA = """
        SELECT
            COUNT(*) AS total,
            SUM(pulgadas       IS NOT NULL) AS pulgadas,
            SUM(ram_gb         IS NOT NULL) AS ram_gb,
            SUM(capacidad_gb   IS NOT NULL) AS capacidad_gb,
            SUM(refresh_hz     IS NOT NULL) AS refresh_hz,
            SUM(bateria_mah    IS NOT NULL) AS bateria_mah,
            SUM(camara_mp      IS NOT NULL) AS camara_mp,
            SUM(potencia_w     IS NOT NULL) AS potencia_w,
            SUM(capacidad_kg   IS NOT NULL) AS capacidad_kg,
            SUM(sistema_operativo IS NOT NULL) AS sistema_operativo,
            SUM(tipo_panel     IS NOT NULL) AS tipo_panel,
            SUM(resolucion     IS NOT NULL) AS resolucion,
            SUM(soporta_5g     IS NOT NULL) AS soporta_5g,
            SUM(gpu            IS NOT NULL) AS gpu
        FROM productos
        WHERE activo = 1
    """

    COBERTURA_POR_CATEGORIA = """
        SELECT
            categoria,
            COUNT(*) AS total,
            SUM(pulgadas       IS NOT NULL) AS pulgadas,
            SUM(ram_gb         IS NOT NULL) AS ram_gb,
            SUM(capacidad_gb   IS NOT NULL) AS capacidad_gb,
            SUM(refresh_hz     IS NOT NULL) AS refresh_hz,
            SUM(bateria_mah    IS NOT NULL) AS bateria_mah,
            SUM(camara_mp      IS NOT NULL) AS camara_mp,
            SUM(potencia_w     IS NOT NULL) AS potencia_w,
            SUM(capacidad_kg   IS NOT NULL) AS capacidad_kg,
            SUM(sistema_operativo IS NOT NULL) AS sistema_operativo,
            SUM(tipo_panel     IS NOT NULL) AS tipo_panel,
            SUM(resolucion     IS NOT NULL) AS resolucion,
            SUM(soporta_5g     IS NOT NULL) AS soporta_5g,
            SUM(gpu            IS NOT NULL) AS gpu
        FROM productos
        WHERE activo = 1
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT 50
    """

    PRODUCTOS_CON_COLUMNAS_VACIAS = """
        SELECT sku, nombre, descripcion, atributos_texto
        FROM productos
        WHERE activo = 1
          AND (
              pulgadas IS NULL OR ram_gb IS NULL OR capacidad_gb IS NULL
              OR refresh_hz IS NULL OR bateria_mah IS NULL OR camara_mp IS NULL
              OR potencia_w IS NULL OR capacidad_kg IS NULL
              OR sistema_operativo IS NULL OR tipo_panel IS NULL
              OR resolucion IS NULL OR soporta_5g IS NULL
          )
        LIMIT :limite
    """

    ACTUALIZAR_ATRIBUTOS = """
        UPDATE productos SET
            pulgadas          = COALESCE(:pulgadas,          pulgadas),
            ram_gb            = COALESCE(:ram_gb,            ram_gb),
            capacidad_gb      = COALESCE(:capacidad_gb,      capacidad_gb),
            refresh_hz        = COALESCE(:refresh_hz,        refresh_hz),
            bateria_mah       = COALESCE(:bateria_mah,       bateria_mah),
            camara_mp         = COALESCE(:camara_mp,         camara_mp),
            potencia_w        = COALESCE(:potencia_w,        potencia_w),
            capacidad_kg      = COALESCE(:capacidad_kg,      capacidad_kg),
            sistema_operativo = COALESCE(:sistema_operativo, sistema_operativo),
            tipo_panel        = COALESCE(:tipo_panel,        tipo_panel),
            resolucion        = COALESCE(:resolucion,        resolucion),
            soporta_5g        = COALESCE(:soporta_5g,        soporta_5g)
        WHERE sku = :sku
    """
