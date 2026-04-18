-- ============================================================
-- Simulación de la base de datos "real" de Dismac
-- Estructura típica de ERP de ecommerce bolivia
-- ============================================================

CREATE TABLE IF NOT EXISTS categorias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  slug VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS marcas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(50) NOT NULL UNIQUE,
  nombre VARCHAR(255) NOT NULL,
  descripcion TEXT,
  categoria_id INT,
  marca_id INT,
  precio_bob DECIMAL(12,2) NOT NULL,
  precio_anterior_bob DECIMAL(12,2),
  stock INT DEFAULT 0,
  imagen_url VARCHAR(500),
  activo TINYINT(1) DEFAULT 1,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (marca_id) REFERENCES marcas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seeds ----------------------------------------------------

INSERT INTO categorias (nombre, slug) VALUES
  ('Televisores', 'televisores'),
  ('Celulares', 'celulares'),
  ('Laptops', 'laptops'),
  ('Refrigeradores', 'refrigeradores'),
  ('Lavadoras', 'lavadoras'),
  ('Audio', 'audio'),
  ('Cocinas', 'cocinas'),
  ('Aires Acondicionados', 'aires-acondicionados'),
  ('Gaming', 'gaming'),
  ('Electrodomésticos Pequeños', 'electrodomesticos-pequenos');

INSERT INTO marcas (nombre) VALUES
  ('Samsung'), ('LG'), ('Sony'), ('Apple'), ('Xiaomi'),
  ('HP'), ('Lenovo'), ('Asus'), ('Whirlpool'), ('Mabe'),
  ('Electrolux'), ('JBL'), ('Bose'), ('Oster'), ('Philips');

INSERT INTO productos (sku, nombre, descripcion, categoria_id, marca_id, precio_bob, precio_anterior_bob, stock, imagen_url) VALUES
  ('TV-SAM-55QLED', 'Televisor Samsung QLED 55" 4K Smart TV', 'Televisor Samsung Serie Q60C, pantalla QLED 55 pulgadas, resolución 4K UHD, Tizen OS, HDR10+, 3 HDMI.', 1, 1, 5499.00, 6299.00, 12, 'https://dismac.example/tv-sam-55qled.jpg'),
  ('TV-LG-65OLED', 'Televisor LG OLED evo 65" 4K', 'Televisor LG OLED C3, 65 pulgadas, procesador α9 Gen6, Dolby Vision, webOS.', 1, 2, 12499.00, 13999.00, 5, NULL),
  ('TV-SONY-50X80', 'Televisor Sony BRAVIA 50" 4K', 'Sony X80K LED 4K HDR Google TV 50 pulgadas.', 1, 3, 4299.00, NULL, 8, NULL),
  ('CEL-IPH-15P-256', 'iPhone 15 Pro 256GB Titanio Natural', 'Apple iPhone 15 Pro, 256GB, chip A17 Pro, cámara 48MP, USB-C.', 2, 4, 12999.00, 13499.00, 7, NULL),
  ('CEL-SAM-S24U', 'Samsung Galaxy S24 Ultra 512GB', 'Galaxy S24 Ultra, Snapdragon 8 Gen 3, 12GB RAM, cámara 200MP, S Pen.', 2, 1, 13499.00, NULL, 10, NULL),
  ('CEL-XIA-14', 'Xiaomi 14 256GB', 'Xiaomi 14, Snapdragon 8 Gen 3, 12GB RAM, Leica óptica.', 2, 5, 6299.00, 6999.00, 20, NULL),
  ('LAP-HP-V14', 'Laptop HP Victus 15 i5 16GB 512GB RTX2050', 'HP Victus, Intel Core i5-13420H, 16GB DDR4, SSD 512GB, NVIDIA RTX 2050, 15.6" FHD 144Hz.', 3, 6, 7499.00, 8299.00, 6, NULL),
  ('LAP-LEN-LO5', 'Laptop Lenovo LOQ 15 Ryzen 7 RTX 4060', 'Lenovo LOQ, Ryzen 7 7840HS, 16GB, 1TB SSD, RTX 4060 8GB, 144Hz.', 3, 7, 10999.00, NULL, 4, NULL),
  ('LAP-ASUS-TUFA15', 'Laptop Asus TUF A15 Ryzen 7 RTX 4050', 'ASUS TUF Gaming A15, Ryzen 7, 16GB, 512GB, RTX 4050.', 3, 8, 9499.00, 9999.00, 3, NULL),
  ('REF-WHI-500L', 'Refrigerador Whirlpool 500L No Frost Inverter', 'Refrigerador Whirlpool French Door 500 litros, No Frost, compresor Inverter, dispensador.', 4, 9, 8999.00, 9799.00, 4, NULL),
  ('REF-LG-410L', 'Refrigerador LG 410L Door Cooling', 'LG Top Mount 410L, Door Cooling+, Smart Inverter Compressor.', 4, 2, 5299.00, NULL, 9, NULL),
  ('LAV-SAM-16KG', 'Lavadora Samsung 16kg EcoBubble', 'Samsung EcoBubble 16kg, carga superior, digital inverter.', 5, 1, 4799.00, 5299.00, 7, NULL),
  ('LAV-LG-18KG', 'Lavadora LG 18kg AI DD', 'LG 18kg AI DD, carga superior, TurboWash.', 5, 2, 5499.00, NULL, 5, NULL),
  ('AUD-JBL-FLIP6', 'Parlante JBL Flip 6 Bluetooth', 'Parlante portátil JBL Flip 6, IP67, 12h batería, PartyBoost.', 6, 12, 899.00, 1099.00, 30, NULL),
  ('AUD-SONY-WH1000', 'Audífonos Sony WH-1000XM5', 'Sony WH-1000XM5 Bluetooth con cancelación de ruido.', 6, 3, 2799.00, 2999.00, 8, NULL),
  ('AUD-BOSE-QCE', 'Audífonos Bose QuietComfort Earbuds II', 'Bose QC Earbuds II, cancelación activa de ruido.', 6, 13, 2199.00, NULL, 10, NULL),
  ('COC-MAB-5H', 'Cocina Mabe 5 hornallas a gas', 'Cocina Mabe 5 hornallas, horno a gas, encendido eléctrico, 76cm.', 7, 10, 3299.00, NULL, 6, NULL),
  ('AIRE-LG-12K', 'Aire Acondicionado LG 12000 BTU Dual Inverter', 'LG Dual Inverter 12000 BTU, frío/calor, Wi-Fi.', 8, 2, 3899.00, 4299.00, 8, NULL),
  ('GAM-SONY-PS5', 'Consola PlayStation 5 Slim 1TB', 'PlayStation 5 Slim edición estándar, 1TB SSD, lectora de discos.', 9, 3, 4999.00, NULL, 15, NULL),
  ('ELE-OST-LIC', 'Licuadora Oster Reversible 10 velocidades', 'Oster Clásica, jarra de vidrio, 600W, 10 velocidades.', 10, 14, 449.00, 529.00, 25, NULL),
  ('ELE-PHI-AIR', 'Freidora de Aire Philips 4.1L', 'Philips Airfryer Essential XL, 4.1L, Rapid Air.', 10, 15, 1099.00, 1299.00, 14, NULL);
