#!/usr/bin/env bash
# Deploys all Bolivian slang/context improvements.
# Run from a terminal where `docker` is available.
set -euo pipefail

echo "==> Rebuilding backend..."
cd "$(dirname "$0")/.."
docker compose up -d --build backend

echo "==> Inserting Bolivian synonyms into live DB..."
docker exec asistente_db mariadb -u asistente -pasistente_pass asistente_db -e "
INSERT IGNORE INTO categorias_sinonimos (palabra_clave, palabra_clave_norm, categoria, subcategoria, confianza) VALUES
('plasma','plasma','Televisores',NULL,0.90),
('plasmas','plasmas','Televisores',NULL,0.85),
('pantallaza','pantallaza','Televisores',NULL,0.85),
('pantallazo','pantallazo','Televisores',NULL,0.85),
('pantalla grande','pantalla grande','Televisores',NULL,0.80),
('pantalla plana','pantalla plana','Televisores',NULL,0.85),
('washa','washa','Lavado',NULL,0.95),
('washas','washas','Lavado',NULL,0.90),
('lavarropas','lavarropas','Lavado',NULL,0.90),
('lavarropas automatico','lavarropas automatico','Lavado',NULL,0.95),
('turri','turri','Cocina Menor',NULL,0.90),
('turris','turris','Cocina Menor',NULL,0.85),
('arrocera','arrocera','Cocina Menor',NULL,0.95),
('arroceras','arroceras','Cocina Menor',NULL,0.90),
('multicocina','multicocina','Cocina Menor',NULL,0.90),
('multicooker','multicooker','Cocina Menor',NULL,0.90),
('aparato','aparato','Celulares','Smartphones',0.70),
('aparatos','aparatos','Celulares','Smartphones',0.65),
('telefono inteligente','telefono inteligente','Celulares','Smartphones',0.95),
('maquina','maquina','Laptops',NULL,0.65),
('compu portatil','compu portatil','Laptops',NULL,0.95),
('computadora portatil','computadora portatil','Laptops',NULL,0.95),
('hela','hela','Refrigeración',NULL,0.75),
('hornilla','hornilla','Cocina',NULL,0.90),
('hornillas','hornillas','Cocina',NULL,0.85),
('anafe','anafe','Cocina',NULL,0.85),
('equipo de musica','equipo de musica','Audio',NULL,0.90),
('equipo musica','equipo musica','Audio',NULL,0.85),
('minicomponente','minicomponente','Audio',NULL,0.90),
('minicomponentes','minicomponentes','Audio',NULL,0.85),
('tableta','tableta','Tablets',NULL,0.95),
('tabletas','tabletas','Tablets',NULL,0.90);
SELECT ROW_COUNT() AS sinonimos_insertados;
INSERT IGNORE INTO categorias_relacionadas (categoria_origen, categoria_sugerida, subcategoria_sugerida, razon, prioridad) VALUES
('Congeladora','Refrigeración','Congeladores','congeladora -> linea de congeladores',10),
('Freezer','Refrigeración','Congeladores','freezer -> congeladores',10),
('Washa','Lavado','Lavadoras','washa es slang boliviano para lavadora',10),
('Plasma','Televisores','Smart TV','plasma es TV en Bolivia',10),
('Arrocera','Cocina Menor','Arroceras','arrocera -> linea de arroceras',10),
('Turri','Cocina Menor','Arroceras','turri es slang boliviano para arrocera',10);
SELECT ROW_COUNT() AS relacionadas_insertadas;
"

echo "==> Applying schema migrations..."
docker exec asistente_db mariadb -u asistente -pasistente_pass asistente_db -e "
ALTER TABLE perfiles_sesion ADD COLUMN IF NOT EXISTS ciudad_sesion VARCHAR(50) DEFAULT NULL;
ALTER TABLE perfiles_sesion ADD COLUMN IF NOT EXISTS presupuesto_min_buscado DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE metricas_turno ADD COLUMN IF NOT EXISTS busquedas_sin_resultado TINYINT(1) NOT NULL DEFAULT 0;
"

echo "==> Done. Backend rebuilt + DB synonyms applied."
echo "Run harness: docker exec asistente_backend python scripts/evaluar_conversaciones.py"
