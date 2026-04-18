-- ============================================================
-- Asistente AI Dismac - Schema MariaDB 11
-- DDD: tablas alineadas a agregados del dominio.
-- ============================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Catálogo de productos (agregado Producto)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    sku                     VARCHAR(64)  NOT NULL PRIMARY KEY,
    nombre                  VARCHAR(500) NOT NULL,
    descripcion             TEXT         NULL,
    categoria               VARCHAR(120) NULL,
    subcategoria            VARCHAR(120) NULL,
    marca                   VARCHAR(120) NULL,
    precio_bob              DECIMAL(12,2) NOT NULL,
    precio_anterior_bob     DECIMAL(12,2) NULL,
    stock                   INT          NOT NULL DEFAULT 0,
    imagen_url              TEXT         NULL,
    url_producto            TEXT         NULL,
    activo                  TINYINT(1)   NOT NULL DEFAULT 1,
    origen                  VARCHAR(60)  NULL,
    -- columnas normalizadas (sin tildes, lowercase) que llena la capa de aplicación
    nombre_norm             VARCHAR(500) NULL,
    descripcion_norm        TEXT         NULL,
    marca_norm              VARCHAR(120) NULL,
    categoria_norm          VARCHAR(120) NULL,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    INDEX ix_productos_categoria (categoria),
    INDEX ix_productos_marca     (marca),
    INDEX ix_productos_precio    (precio_bob),
    INDEX ix_productos_activo    (activo, stock),
    FULLTEXT INDEX ft_productos_busqueda (nombre_norm, descripcion_norm, marca_norm, categoria_norm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Sesiones (agregado Sesion)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sesiones (
    id                      CHAR(36)     NOT NULL PRIMARY KEY,
    carrito_estado          ENUM('activo', 'abandonado', 'convertido') NOT NULL DEFAULT 'activo',
    cliente_nombre          VARCHAR(200) NULL,
    cliente_email           VARCHAR(200) NULL,
    cliente_telefono        VARCHAR(40)  NULL,
    ultima_actividad_at     DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    INDEX ix_sesiones_estado (carrito_estado, ultima_actividad_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Mensajes de chat (agregado ConversacionChat)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mensajes (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sesion_id               CHAR(36)     NOT NULL,
    rol                     ENUM('user', 'assistant', 'tool', 'system') NOT NULL,
    contenido               MEDIUMTEXT   NOT NULL,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    INDEX ix_mensajes_sesion (sesion_id, created_at),
    CONSTRAINT fk_mensajes_sesion FOREIGN KEY (sesion_id) REFERENCES sesiones(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Carrito (entity CarritoItem dentro del agregado Carrito)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carrito_items (
    sesion_id               CHAR(36)     NOT NULL,
    sku                     VARCHAR(64)  NOT NULL,
    cantidad                INT          NOT NULL DEFAULT 1,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (sesion_id, sku),
    INDEX ix_carrito_sesion (sesion_id),
    CONSTRAINT fk_carrito_sesion  FOREIGN KEY (sesion_id) REFERENCES sesiones(id)   ON DELETE CASCADE,
    CONSTRAINT fk_carrito_producto FOREIGN KEY (sku)      REFERENCES productos(sku) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Órdenes (agregado Orden, detalle OrdenItem)
-- numero_orden se genera por secuencia MariaDB: DSM-100001, DSM-100002...
-- ------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS ordenes_numero_seq
    START WITH 100001
    MINVALUE 100001
    INCREMENT BY 1
    NOCACHE;

CREATE TABLE IF NOT EXISTS ordenes (
    id                      CHAR(36)     NOT NULL PRIMARY KEY,
    numero_orden            VARCHAR(20)  NOT NULL UNIQUE
                                DEFAULT (CONCAT('DSM-', NEXTVAL(ordenes_numero_seq))),
    sesion_id               CHAR(36)     NOT NULL,
    cliente_nombre          VARCHAR(200) NOT NULL,
    cliente_email           VARCHAR(200) NULL,
    cliente_telefono        VARCHAR(40)  NULL,
    cliente_ciudad          VARCHAR(120) NULL DEFAULT 'Santa Cruz',
    total_bob               DECIMAL(12,2) NOT NULL,
    items_cantidad          INT          NOT NULL,
    estado                  ENUM('confirmada', 'enviada', 'entregada', 'cancelada') NOT NULL DEFAULT 'confirmada',
    notas                   TEXT         NULL,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    INDEX ix_ordenes_sesion  (sesion_id),
    INDEX ix_ordenes_estado  (estado, created_at),
    CONSTRAINT fk_ordenes_sesion FOREIGN KEY (sesion_id) REFERENCES sesiones(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orden_items (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    orden_id                CHAR(36)     NOT NULL,
    sku                     VARCHAR(64)  NOT NULL,
    nombre                  VARCHAR(500) NOT NULL,
    marca                   VARCHAR(120) NULL,
    cantidad                INT          NOT NULL,
    precio_unitario_bob     DECIMAL(12,2) NOT NULL,
    subtotal_bob            DECIMAL(12,2) NOT NULL,

    INDEX ix_orden_items_orden (orden_id),
    CONSTRAINT fk_orden_items_orden FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Log de ingestas (auditoría del ingestor)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestas_log (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    origen                  VARCHAR(60)  NOT NULL,
    inicio                  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    fin                     DATETIME(6)  NULL,
    estado                  ENUM('en_curso', 'ok', 'error') NOT NULL DEFAULT 'en_curso',
    productos_procesados    INT          NOT NULL DEFAULT 0,
    error                   TEXT         NULL,

    INDEX ix_ingestas_origen (origen, inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Vista de lectura para el modelo CQRS (query side)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vista_carritos AS
SELECT
    s.id                            AS sesion_id,
    s.carrito_estado                AS estado,
    s.cliente_nombre,
    s.cliente_email,
    s.cliente_telefono,
    s.ultima_actividad_at,
    COUNT(ci.sku)                   AS items,
    COALESCE(SUM(ci.cantidad * p.precio_bob), 0) AS total_bob
FROM sesiones s
LEFT JOIN carrito_items ci ON ci.sesion_id = s.id
LEFT JOIN productos p      ON p.sku = ci.sku
GROUP BY s.id, s.carrito_estado, s.cliente_nombre, s.cliente_email,
         s.cliente_telefono, s.ultima_actividad_at;
