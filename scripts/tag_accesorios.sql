-- Marca productos como accesorios usando patrones de nombre y tipo_producto.
-- Idempotente: se puede correr multiples veces sin efectos secundarios.
-- Uso:
--   docker compose exec -T db mariadb -u asistente -pasistente_pass asistente_db < scripts/tag_accesorios.sql

UPDATE productos SET es_accesorio = 1
WHERE activo = 1 AND es_accesorio = 0 AND (
    LOWER(nombre) REGEXP '^(mochila|maletin|funda|estuche|carcasa|cartucho|toner|correa|stylus|mousepad|mouse pad|pelicula|mica|adaptador|repuesto|dock|protector de pantalla|cable |cargador |organizador |organizadores |porta |jarra )'
    OR LOWER(nombre) LIKE 'base para notebook%'
    OR LOWER(nombre) LIKE 'base para laptop%'
    OR LOWER(nombre) LIKE 'soporte para %'
    OR LOWER(nombre) LIKE 'soporte ajustable%'
    OR LOWER(nombre) LIKE 'soporte laptop%'
    OR LOWER(nombre) LIKE '% soporte laptop%'
    OR LOWER(nombre) LIKE 'porta%huevo%'
    OR LOWER(nombre) LIKE 'organizador%de nevera%'
    OR LOWER(nombre) LIKE 'organizadores%nevera%'
    OR LOWER(nombre) LIKE 'set %cubiertas%perrilla%'
    OR LOWER(nombre) LIKE 'tinta %'
    OR LOWER(nombre) LIKE 'control remoto%'
    OR LOWER(nombre) LIKE 'filtro %'
    OR LOWER(nombre) LIKE 'correa %'
    OR tipo_producto IN (
        'mochila','mochilas','mochila con ruedas','maletin','funda','estuche',
        'cartucho','toner','cable','adaptador','cargador','soporte',
        'protector de pantalla','mica','pelicula','control remoto'
    )
);

-- Clasifica impresoras térmicas (POS/recibos/etiquetas) bajo tipo_producto
-- para que el DetectorExclusionesMensaje las excluya de búsquedas genéricas
-- ("impresora" sin calificador "termica/pos").
UPDATE productos SET tipo_producto = 'impresora_termica'
WHERE activo = 1 AND LOWER(nombre) LIKE '%impresora%termic%'
  AND (tipo_producto IS NULL OR tipo_producto != 'impresora_termica');

SELECT SUM(es_accesorio) AS accesorios_tagueados FROM productos WHERE activo = 1;
