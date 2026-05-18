"""V002 — Seed inicial: sinónimos de categorías y relaciones cross-categoría.

Datos semilla que el resolvedor de categorías necesita desde el primer
arranque. Son idempotentes (INSERT IGNORE) y se pueden re-ejecutar sin riesgo.

Revision ID: V002
Revises: V001
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "V002"
down_revision = "V001"
branch_labels = None
depends_on = None

# Bloques separados para legibilidad; todos usan INSERT IGNORE.
_SINONIMOS_PRINCIPALES = """
INSERT IGNORE INTO categorias_sinonimos (palabra_clave,palabra_clave_norm,categoria,subcategoria,confianza) VALUES
('audifono','audifono','Audio',NULL,1.00),('audifonos','audifonos','Audio',NULL,1.00),
('auricular','auricular','Audio',NULL,1.00),('auriculares','auriculares','Audio',NULL,1.00),
('barra de sonido','barra de sonido','Audio',NULL,1.00),('bocina','bocina','Audio',NULL,1.00),
('parlante','parlante','Audio',NULL,1.00),('soundbar','soundbar','Audio',NULL,1.00),
('casco moto','casco moto','Automotriz','Motos',1.00),('moto','moto','Automotriz','Vehículos',1.00),
('motocicleta','motocicleta','Automotriz','Vehículos',1.00),('scooter','scooter','Automotriz','Vehículos',1.00),
('celular','celular','Celulares','Smartphones',1.00),('celulares','celulares','Celulares','Smartphones',0.99),
('iphone','iphone','Celulares','Smartphones',1.00),('smartphone','smartphone','Celulares','Smartphones',1.00),
('telefono','telefono','Celulares','Smartphones',0.90),('telefonos','telefonos','Celulares','Smartphones',0.95),
('aire acondicionado','aire acondicionado','Climatización',NULL,1.00),
('calefactor','calefactor','Climatización',NULL,1.00),('ventilador','ventilador','Climatización',NULL,1.00),
('cocina a gas','cocina a gas','Cocina',NULL,1.00),('cocina electrica','cocina electrica','Cocina',NULL,1.00),
('airfryer','airfryer','Cocina Menor',NULL,1.00),('batidora','batidora','Cocina Menor',NULL,1.00),
('cafetera','cafetera','Cocina Menor',NULL,1.00),('freidora','freidora','Cocina Menor',NULL,1.00),
('licuadora','licuadora','Cocina Menor',NULL,1.00),('microondas','microondas','Cocina Menor',NULL,1.00),
('olla arrocera','olla arrocera','Cocina Menor',NULL,1.00),('tostadora','tostadora','Cocina Menor',NULL,1.00),
('desktop','desktop','Computación',NULL,1.00),('monitor','monitor','Computación',NULL,1.00),
('pc','pc','Computación',NULL,1.00),('teclado','teclado','Computación',NULL,1.00),
('laptop','laptop','Laptops',NULL,1.00),('laptops','laptops','Laptops',NULL,0.99),
('macbook','macbook','Laptops',NULL,1.00),('notebook','notebook','Laptops',NULL,1.00),
('portatil','portatil','Laptops',NULL,1.00),('ultrabook','ultrabook','Laptops',NULL,1.00),
('lavadora','lavadora','Lavado',NULL,1.00),('secadora','secadora','Lavado',NULL,1.00),
('refrigerador','refrigerador','Refrigeración',NULL,1.00),('congelador','congelador','Refrigeración',NULL,1.00),
('frigobar','frigobar','Refrigeración',NULL,1.00),('nevera','nevera','Refrigeración',NULL,1.00),
('reloj','reloj','Relojería',NULL,0.90),('relojes','relojes','Relojería',NULL,0.95),
('reloj inteligente','reloj inteligente','Smartwatch',NULL,1.00),('smartwatch','smartwatch','Smartwatch',NULL,1.00),
('ipad','ipad','Tablets',NULL,1.00),('tablet','tablet','Tablets',NULL,1.00),
('smart tv','smart tv','Televisores',NULL,1.00),('television','television','Televisores',NULL,1.00),
('televisor','televisor','Televisores',NULL,1.00),('tv','tv','Televisores',NULL,1.00),
('consola','consola','Gaming',NULL,1.00),('ps5','ps5','Gaming',NULL,1.00),
('xbox','xbox','Gaming',NULL,1.00),('nintendo','nintendo','Gaming',NULL,1.00),
('impresora','impresora','Impresión',NULL,1.00),('juguete','juguete','Juguetería',NULL,1.00),
('aspiradora','aspiradora','Pequeños Electrodomésticos',NULL,1.00),
('plancha de ropa','plancha de ropa','Pequeños Electrodomésticos',NULL,1.00),
('camara','camara','Fotografía',NULL,1.00),('drone','drone','Fotografía',NULL,0.80),
('bicicleta','bicicleta','Deportes',NULL,0.90),('pesas','pesas','Deportes',NULL,1.00),
('taladro','taladro','Herramientas',NULL,1.00),
('cama','cama','Muebles',NULL,1.00),('escritorio','escritorio','Muebles',NULL,1.00),
('sofa','sofa','Muebles',NULL,1.00),('sillon','sillon','Muebles',NULL,1.00)
"""

_SINONIMOS_BOLIVIANOS = """
INSERT IGNORE INTO categorias_sinonimos (palabra_clave,palabra_clave_norm,categoria,subcategoria,confianza) VALUES
('plasma','plasma','Televisores',NULL,0.90),('pantallaza','pantallaza','Televisores',NULL,0.85),
('washa','washa','Lavado',NULL,0.95),('lavarropas','lavarropas','Lavado',NULL,0.90),
('turri','turri','Cocina Menor',NULL,0.90),('arrocera','arrocera','Cocina Menor',NULL,0.95),
('multicocina','multicocina','Cocina Menor',NULL,0.90),
('aparato','aparato','Celulares','Smartphones',0.70),
('telefono inteligente','telefono inteligente','Celulares','Smartphones',0.95),
('maquina','maquina','Laptops',NULL,0.65),('computadora portatil','computadora portatil','Laptops',NULL,0.95),
('hela','hela','Refrigeración',NULL,0.75),('heladera','heladera','Refrigeración',NULL,1.00),
('hornilla','hornilla','Cocina',NULL,0.90),('anafe','anafe','Cocina',NULL,0.85),
('equipo de musica','equipo de musica','Audio',NULL,0.90),
('minicomponente','minicomponente','Audio',NULL,0.90),
('tableta','tableta','Tablets',NULL,0.95),
('lapto','lapto','Laptops',NULL,0.92),('chrombuk','chrombuk','Laptops','Chromebooks',0.88),
('chromebook','chromebook','Laptops','Chromebooks',0.95),('netbook','netbook','Laptops',NULL,0.90),
('frigo','frigo','Refrigeración',NULL,0.80)
"""

_RELACIONADAS = """
INSERT IGNORE INTO categorias_relacionadas (categoria_origen,categoria_sugerida,subcategoria_sugerida,razon,prioridad) VALUES
('Aire','Climatización','Aire Acondicionado','linea de aire acondicionado',10),
('Auto','Automotriz','Vehículos','no vendemos autos pero si motocicletas',10),
('Automoviles','Automotriz','Vehículos','no vendemos autos pero si motocicletas',10),
('Bicicleta','Deportes','Bicicletas','linea de bicicletas',10),
('Camara','Fotografía','Cámaras','camaras de fotografia',30),
('Camara','Seguridad','Cámaras de Seguridad','camaras de seguridad',40),
('Colchon','Muebles','Colchones','linea de colchones',10),
('Computador','Laptops','Notebooks','notebooks / laptops',20),
('Freidora','Pequeños Electrodomésticos','Freidoras','linea de freidoras sin aceite',10),
('Galaxy','Celulares','Smartphones','tenemos varios modelos Samsung Galaxy',20),
('Horno','Cocina','Hornos','hornos empotrables y de sobremesa',10),
('Iphone','Celulares','Smartphones','tenemos smartphones equivalentes',20),
('Licuadora','Pequeños Electrodomésticos','Licuadoras','linea de licuadoras',10),
('Microondas','Cocina','Microondas','linea de microondas',10),
('Monitor','Computación','Monitores','linea de monitores PC',10),
('Nevera','Refrigeración','Refrigeradores','linea de refrigeradores',10),
('Nintendo','Gaming','Consolas','linea de consolas Nintendo',10),
('PC','Computación','PC Escritorio','PCs de escritorio',10),
('PlayStation','Gaming','Consolas','linea de consolas PlayStation',10),
('PS5','Gaming','Consolas','consolas PlayStation',10),
('Refrigerador','Refrigeración','Refrigeradores','linea de refrigeradores',10),
('Reloj','Relojería','Relojes','linea de relojes',10),
('Sofa','Muebles','Muebles','linea de muebles de sala',10),
('Taladro','Herramientas','Taladros','linea de taladros',10),
('Tesla','Automotriz','Vehículos','no vendemos Tesla pero si motocicletas electricas',20),
('Ventilador','Climatización','Ventiladores','linea de ventiladores',10),
('Xbox','Gaming','Consolas','linea de consolas Xbox',10),
('Xiaomi','Celulares','Smartphones','tenemos varios modelos Xiaomi',20),
('Washa','Lavado','Lavadoras','washa es slang boliviano para lavadora',10),
('Plasma','Televisores','Smart TV','plasma es TV en Bolivia',10),
('Arrocera','Cocina Menor','Arroceras','arrocera -> linea de arroceras',10),
('Turri','Cocina Menor','Arroceras','turri es slang boliviano para arrocera',10),
('Toyota','Automotriz','Vehículos','no vendemos Toyota pero si motocicletas electricas',20),
('Honda','Automotriz','Vehículos','no vendemos autos Honda pero si motocicletas',25),
('Yamaha','Automotriz','Vehículos','yamaha es de motos, tenemos motocicletas Bajaj y Sunra',15),
('BMW','Automotriz','Vehículos','no vendemos BMW pero si motocicletas electricas',20),
('Mercedes','Automotriz','Vehículos','no vendemos Mercedes pero si motocicletas electricas',20)
"""


def upgrade() -> None:
    op.execute(text(_SINONIMOS_PRINCIPALES))
    op.execute(text(_SINONIMOS_BOLIVIANOS))
    op.execute(text(_RELACIONADAS))


def downgrade() -> None:
    op.execute(text("DELETE FROM categorias_relacionadas"))
    op.execute(text("DELETE FROM categorias_sinonimos"))
