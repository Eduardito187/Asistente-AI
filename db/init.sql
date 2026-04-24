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
    -- atributos estructurados extraidos del nombre/descripcion durante la ingesta.
    -- Permiten filtros exactos (p.ej. pulgadas=85) sin depender del FULLTEXT.
    pulgadas                DECIMAL(5,1) NULL,
    capacidad_gb            INT          NULL,
    ram_gb                  INT          NULL,
    capacidad_litros        DECIMAL(7,2) NULL,
    capacidad_kg            DECIMAL(5,1) NULL,
    potencia_w              INT          NULL,
    procesador              VARCHAR(50)  NULL,
    color                   VARCHAR(40)  NULL,
    tipo_panel              VARCHAR(20)  NULL,
    resolucion              VARCHAR(10)  NULL,
    es_electrico            TINYINT(1)   NULL,
    -- Specs adicionales para comparativas (ingestor las llena cuando puede
    -- parsearlas del detalle; el extractor regex las infiere de nombre+desc
    -- como fallback).
    bateria_mah             INT          NULL,
    camara_mp               SMALLINT     NULL,
    camara_frontal_mp       SMALLINT     NULL,
    soporta_5g              TINYINT(1)   NULL,
    sistema_operativo       VARCHAR(30)  NULL,
    refresh_hz              SMALLINT     NULL,
    gpu                     VARCHAR(60)  NULL,
    -- Marca accesorios "hijos" de otra categoria (ej. correa smartwatch, funda
    -- celular). Permite separarlos del listado principal y proponerlos como
    -- cross-sell. Productos cuya subcategoria ya es de accesorios NO llevan
    -- este flag (ellos son el producto principal de su subcategoria).
    es_accesorio            TINYINT(1)   NOT NULL DEFAULT 0,
    -- Producto dado de baja del catálogo online (Clacom='Cat. X - Descontinuado' en Akeneo).
    -- Puede buscarse pero NO se ofrece compra online: el agente redirige a tienda física.
    es_descontinuado        TINYINT(1)   NOT NULL DEFAULT 0,
    -- Audiencia de genero cuando el nombre o descripcion lo marca explicitamente
    -- (ej. "reloj para mujer", "cepillo electrico para hombre"). NULL = sin marca,
    -- se considera neutro/unisex. Sirve para filtrar busquedas tipo "para mujer"
    -- sin adivinar por color u otra heuristica fragil.
    genero                  ENUM('masculino','femenino','unisex','infantil') NULL,
    -- Subtipo fino dentro de la categoria: permite separar "reloj pulsera" de
    -- "reloj pared" o "parlante portatil" de "soundbar" sin subcategoria nueva.
    -- Vocabulario por categoria:
    --   Relojeria: pulsera | pared | despertador | smart | decorativo
    --   Audio:     parlante | audifono | soundbar | portatil
    --   Computo:   desktop | notebook | all_in_one
    -- NULL = sin clasificar (el ingestor lo llena a partir del nuevo Excel).
    tipo_producto           VARCHAR(40)  NULL,
    -- Indica que el producto se lleva puesto (smartwatch, reloj pulsera, auricular
    -- bluetooth). Permite filtrar "un reloj para la muneca" = es_vestible = 1.
    es_vestible             TINYINT(1)   NULL,
    -- ---------------------------------------------------------------
    -- Campos de alto fill-rate de Akeneo (presentes en >25% del catálogo)
    -- Se mantienen como columnas fijas para evitar JSON_EXTRACT en filtros.
    -- ---------------------------------------------------------------
    -- Número de modelo del fabricante (ej. "Galaxy S26 Ultra", "WH-1000XM5")
    modelo                  VARCHAR(120) NULL,
    -- Meses de garantía oficial Dismac
    meses_garantia          SMALLINT     NULL,
    -- Texto comercial largo (Speach Comercial de Akeneo) — para comparativas del LLM
    descripcion_extendida   TEXT         NULL,
    -- Bullets de características únicas separados por "|" (Característica 1..5)
    caracteristicas         TEXT         NULL,
    -- ---------------------------------------------------------------
    -- Atributos dinámicos: almacén flexible para cualquier atributo
    -- de Akeneo que no tenga columna fija. El ingestor vuelca aquí
    -- todo lo demás como {"Potencia": "1500W", "Color de luz": "Blanco", ...}.
    -- Nunca hay que hacer ALTER TABLE para agregar un atributo nuevo.
    -- ---------------------------------------------------------------
    atributos               JSON         NULL,
    -- Versión plana de `atributos` para FULLTEXT: "Potencia: 1500W\nColor: Blanco\n..."
    -- El ingestor la regenera cada vez que actualiza el JSON.
    -- Incluida en ft_productos_busqueda para que el agente encuentre
    -- specs como "1500W", "noise cancelling" o "inverter" en texto libre.
    atributos_texto         TEXT         NULL,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    INDEX ix_productos_categoria (categoria),
    INDEX ix_productos_marca     (marca),
    INDEX ix_productos_precio    (precio_bob),
    INDEX ix_productos_activo    (activo, stock),
    INDEX ix_productos_pulgadas  (pulgadas),
    INDEX ix_productos_capacidad (capacidad_gb),
    INDEX ix_productos_es_accesorio (es_accesorio, categoria, subcategoria),
    INDEX ix_productos_genero (genero, categoria, subcategoria),
    INDEX ix_productos_tipo_producto (tipo_producto, categoria),
    INDEX ix_productos_es_vestible (es_vestible, categoria),
    INDEX ix_productos_modelo (modelo),
    FULLTEXT INDEX ft_productos_busqueda (nombre_norm, descripcion_norm, marca_norm, categoria_norm, atributos_texto),
    -- Indice usado por el buscador principal: excluye descripcion_norm para
    -- evitar falsos positivos (p.ej. 'soporte de pared para tv' matcheando 'tv').
    FULLTEXT INDEX ft_productos_nombre (nombre_norm, marca_norm, categoria_norm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Catálogo de atributos por categoría (registro dinámico)
-- Permite que el sistema sepa qué atributos existen para cada
-- categoría sin leer todos los JSON de productos. El ingestor
-- hace upsert aquí cada vez que procesa el CSV de Akeneo.
-- El agente puede consultarlo para saber qué filtros ofrecer.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS catalogo_atributos (
    id                      INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    categoria               VARCHAR(120) NOT NULL,
    subcategoria            VARCHAR(120) NULL,
    nombre                  VARCHAR(200) NOT NULL,
    -- Tipo del valor para orientar el frontend/agente
    tipo_valor              ENUM('texto','numero','booleano','lista') NOT NULL DEFAULT 'texto',
    -- Unidad de medida si aplica (W, kg, pulgadas, mAh…)
    unidad                  VARCHAR(20)  NULL,
    -- Cuántos productos activos tienen este atributo (se actualiza en cada ingesta)
    conteo_productos        INT          NOT NULL DEFAULT 0,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    UNIQUE INDEX uq_atributo_cat (categoria, subcategoria, nombre),
    INDEX ix_atributo_categoria (categoria),
    INDEX ix_atributo_conteo (conteo_productos DESC)
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
-- Sugerencias de catálogo (productos reales pedidos por clientes
-- pero aún no presentes en el catálogo).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sugerencias_catalogo (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre                  VARCHAR(300) NOT NULL,
    nombre_norm             VARCHAR(300) NOT NULL,
    categoria_estimada      VARCHAR(120) NULL,
    marca_estimada          VARCHAR(120) NULL,
    veces_solicitado        INT          NOT NULL DEFAULT 1,
    primer_contexto_cliente TEXT         NULL,
    primera_fecha           DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    ultima_fecha            DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    UNIQUE KEY uk_sugerencias_nombre_norm (nombre_norm),
    INDEX ix_sugerencias_ultima_fecha (ultima_fecha),
    INDEX ix_sugerencias_veces (veces_solicitado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Conversaciones curadas: ejemplos "buenos" usados como few-shot
-- dinámico para mejorar el tono y la eficiencia del asistente.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversaciones_curadas (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sesion_id               CHAR(36)     NULL,
    etiqueta                VARCHAR(120) NULL,
    cliente_texto           MEDIUMTEXT   NOT NULL,
    asistente_texto         MEDIUMTEXT   NOT NULL,
    score                   INT          NOT NULL DEFAULT 0,
    turnos                  INT          NOT NULL DEFAULT 0,
    llevo_a_orden           TINYINT(1)   NOT NULL DEFAULT 0,
    activa                  TINYINT(1)   NOT NULL DEFAULT 1,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    UNIQUE KEY uk_conv_curada_sesion (sesion_id),
    INDEX ix_conv_curada_activa_score (activa, score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Metricas por turno (para dashboards y ajuste de latencia).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_turno (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sesion_id               CHAR(36)     NOT NULL,
    mensaje_usuario_len     INT          NOT NULL DEFAULT 0,
    respuesta_len           INT          NOT NULL DEFAULT 0,
    tool_calls              INT          NOT NULL DEFAULT 0,
    mentiras_detectadas     INT          NOT NULL DEFAULT 0,
    productos_citados       INT          NOT NULL DEFAULT 0,
    ruta                    VARCHAR(40)  NOT NULL DEFAULT 'agente',
    tiempo_ms               INT          NOT NULL DEFAULT 0,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    INDEX ix_metricas_sesion (sesion_id, created_at),
    INDEX ix_metricas_ruta (ruta, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Perfil de sesión: preferencias declaradas por el cliente durante el chat
-- (presupuesto, marca favorita, categoría de interés, uso).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perfiles_sesion (
    sesion_id               CHAR(36)     NOT NULL PRIMARY KEY,
    presupuesto_max         DECIMAL(12,2) NULL,
    marca_preferida         VARCHAR(120) NULL,
    categoria_foco          VARCHAR(120) NULL,
    subcategoria_foco       VARCHAR(120) NULL,
    sku_foco                VARCHAR(64)  NULL,
    genero_declarado        VARCHAR(20)  NULL,
    desired_tier            VARCHAR(20)  NULL,
    uso_declarado           VARCHAR(200) NULL,
    pulgadas                DECIMAL(4,1) NULL,
    tipo_panel              VARCHAR(32)  NULL,
    resolucion              VARCHAR(16)  NULL,
    ultimos_skus_mostrados  TEXT         NULL,
    precio_min_mostrado     DECIMAL(12,2) NULL,
    precio_max_mostrado     DECIMAL(12,2) NULL,
    alternativa_ofrecida    VARCHAR(240) NULL,
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT fk_perfil_sesion FOREIGN KEY (sesion_id) REFERENCES sesiones(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Feedback post-orden: rating + comentario del cliente tras cerrar.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback_ordenes (
    id                      BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    orden_id                CHAR(36)     NOT NULL,
    sesion_id               CHAR(36)     NOT NULL,
    rating                  TINYINT      NULL,
    comentario              TEXT         NULL,
    created_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    UNIQUE KEY uk_feedback_orden (orden_id),
    INDEX ix_feedback_sesion (sesion_id),
    CONSTRAINT fk_feedback_orden  FOREIGN KEY (orden_id)  REFERENCES ordenes(id)  ON DELETE CASCADE,
    CONSTRAINT fk_feedback_sesion FOREIGN KEY (sesion_id) REFERENCES sesiones(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Embeddings de productos: vector serializado (float32) + modelo usado.
-- Se consulta fuera de MariaDB (cosine similarity en memoria).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos_embeddings (
    sku                     VARCHAR(64)  NOT NULL PRIMARY KEY,
    modelo                  VARCHAR(80)  NOT NULL,
    `vector`                BLOB         NOT NULL,
    updated_at              DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT fk_emb_producto FOREIGN KEY (sku) REFERENCES productos(sku) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Sinónimos y palabras clave -> categoría del catálogo.
-- Fuente única de verdad para resolver "auto", "tesla", "motocicleta",
-- "freidora", etc. a una categoria/subcategoria REAL del catálogo.
-- El LLM no debe negar ni inventar categorias: siempre leer de aqui.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias_sinonimos (
    id                      INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    palabra_clave           VARCHAR(80)  NOT NULL,
    palabra_clave_norm      VARCHAR(80)  NOT NULL,
    categoria               VARCHAR(120) NOT NULL,
    subcategoria            VARCHAR(120) NULL,
    -- SKU concreto cuando el alias identifica univocamente un producto
    -- (ej. "s26 ultra" -> SM-S948BZKKBVO). Si es NULL, el alias apunta
    -- solo a la categoria/subcategoria.
    sku_especifico          VARCHAR(64)  NULL,
    confianza               DECIMAL(3,2) NOT NULL DEFAULT 1.00,

    UNIQUE KEY uq_palabra_norm (palabra_clave_norm),
    INDEX ix_cat_sinonimos_categoria (categoria),
    INDEX ix_sinonimos_sku (sku_especifico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Relaciones cross-categoria: si el cliente pide algo de la
-- categoria_origen y no existe, se ofrece categoria_sugerida.
-- Ej: origen="Automoviles" (inexistente) -> sugerida="Automotriz"
--     subcategoria_sugerida="Vehículos" (motocicletas reales).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias_relacionadas (
    categoria_origen        VARCHAR(120) NOT NULL,
    categoria_sugerida      VARCHAR(120) NOT NULL,
    subcategoria_sugerida   VARCHAR(120) NULL,
    razon                   VARCHAR(200) NOT NULL,
    prioridad               INT          NOT NULL DEFAULT 100,

    PRIMARY KEY (categoria_origen, categoria_sugerida)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Seed de sinonimos (fuente unica de verdad para resolver lenguaje del cliente)
INSERT IGNORE INTO categorias_sinonimos (palabra_clave, palabra_clave_norm, categoria, subcategoria, confianza) VALUES
('audifono','audifono','Audio',NULL,1.00),
('audifonos','audifonos','Audio',NULL,1.00),
('auricular','auricular','Audio',NULL,1.00),
('auriculares','auriculares','Audio',NULL,1.00),
('barra de sonido','barra de sonido','Audio',NULL,1.00),
('barras de sonido','barras de sonido','Audio',NULL,0.95),
('bocina','bocina','Audio',NULL,1.00),
('bocinas','bocinas','Audio',NULL,0.90),
('parlante','parlante','Audio',NULL,1.00),
('parlantes','parlantes','Audio',NULL,0.95),
('soundbar','soundbar','Audio',NULL,1.00),
('soundbars','soundbars','Audio',NULL,0.95),
('casco','casco','Automotriz','Motos',0.90),
('casco moto','casco moto','Automotriz','Motos',1.00),
('cascos','cascos','Automotriz','Motos',0.85),
('cascos moto','cascos moto','Automotriz','Motos',0.95),
('ciclomotor','ciclomotor','Automotriz','Vehículos',1.00),
('ciclomotores','ciclomotores','Automotriz','Vehículos',0.95),
('cobertor auto','cobertor auto','Automotriz','Accesorios Auto',1.00),
('cobertores auto','cobertores auto','Automotriz','Accesorios Auto',0.95),
('cubreasiento','cubreasiento','Automotriz','Accesorios Auto',1.00),
('cubreasientos','cubreasientos','Automotriz','Accesorios Auto',0.95),
('llanta moto','llanta moto','Automotriz','Motos',1.00),
('llantas moto','llantas moto','Automotriz','Motos',0.95),
('moto','moto','Automotriz','Vehículos',1.00),
('motocicleta','motocicleta','Automotriz','Vehículos',1.00),
('motocicletas','motocicletas','Automotriz','Vehículos',0.99),
('motos','motos','Automotriz','Vehículos',0.98),
('scooter','scooter','Automotriz','Vehículos',1.00),
('scooters','scooters','Automotriz','Vehículos',0.95),
('coche bebe','coche bebe','Bebés',NULL,1.00),
('cochecito','cochecito','Bebés',NULL,1.00),
('cochecitos','cochecitos','Bebés',NULL,0.95),
('coches bebe','coches bebe','Bebés',NULL,0.95),
('cuna','cuna','Bebés',NULL,1.00),
('cunas','cunas','Bebés',NULL,0.95),
('silla auto bebe','silla auto bebe','Bebés',NULL,1.00),
('sillas auto bebe','sillas auto bebe','Bebés',NULL,0.95),
('celular','celular','Celulares','Smartphones',1.00),
('celulares','celulares','Celulares','Smartphones',0.99),
('iphone','iphone','Celulares','Smartphones',1.00),
('iphones','iphones','Celulares','Smartphones',0.95),
('movil','movil','Celulares','Smartphones',1.00),
('moviles','moviles','Celulares','Smartphones',0.90),
('smartphone','smartphone','Celulares','Smartphones',1.00),
('smartphones','smartphones','Celulares','Smartphones',0.95),
('telefono','telefono','Celulares','Smartphones',0.90),
('telefonos','telefonos','Celulares','Smartphones',0.95),
('aire acondicionado','aire acondicionado','Climatización',NULL,1.00),
('aires acondicionados','aires acondicionados','Climatización',NULL,0.95),
('calefactor','calefactor','Climatización',NULL,1.00),
('calefactores','calefactores','Climatización',NULL,0.95),
('estufa','estufa','Climatización',NULL,0.90),
('estufas','estufas','Climatización',NULL,0.95),
('ventilador','ventilador','Climatización',NULL,1.00),
('ventiladores','ventiladores','Climatización',NULL,0.95),
('cocina a gas','cocina a gas','Cocina',NULL,1.00),
('cocina electrica','cocina electrica','Cocina',NULL,1.00),
('cocinas a gas','cocinas a gas','Cocina',NULL,0.95),
('cocinas electricas','cocinas electricas','Cocina',NULL,0.95),
('horno','horno','Cocina',NULL,0.90),
('hornos','hornos','Cocina',NULL,0.90),
('airfryer','airfryer','Cocina Menor',NULL,1.00),
('airfryers','airfryers','Cocina Menor',NULL,0.95),
('batidora','batidora','Cocina Menor',NULL,1.00),
('batidoras','batidoras','Cocina Menor',NULL,0.95),
('cafetera','cafetera','Cocina Menor',NULL,1.00),
('cafeteras','cafeteras','Cocina Menor',NULL,0.95),
('freidora','freidora','Cocina Menor',NULL,1.00),
('freidoras','freidoras','Cocina Menor',NULL,0.95),
('horno electrico','horno electrico','Cocina Menor',NULL,1.00),
('hornos electricos','hornos electricos','Cocina Menor',NULL,0.95),
('licuadora','licuadora','Cocina Menor',NULL,1.00),
('licuadoras','licuadoras','Cocina Menor',NULL,0.95),
('microondas','microondas','Cocina Menor',NULL,1.00),
('olla arrocera','olla arrocera','Cocina Menor',NULL,1.00),
('ollas arroceras','ollas arroceras','Cocina Menor',NULL,0.95),
('sandwichera','sandwichera','Cocina Menor',NULL,1.00),
('sandwicheras','sandwicheras','Cocina Menor',NULL,0.95),
('tostadora','tostadora','Cocina Menor',NULL,1.00),
('tostadoras','tostadoras','Cocina Menor',NULL,0.95),
('desktop','desktop','Computación',NULL,1.00),
('desktops','desktops','Computación',NULL,0.90),
('monitor','monitor','Computación',NULL,1.00),
('monitores','monitores','Computación',NULL,0.95),
('mouse','mouse','Computación',NULL,1.00),
('pc','pc','Computación',NULL,1.00),
('pcs','pcs','Computación',NULL,0.85),
('teclado','teclado','Computación',NULL,1.00),
('teclados','teclados','Computación',NULL,0.95),
('afeitadora','afeitadora','Cuidado Personal',NULL,1.00),
('afeitadoras','afeitadoras','Cuidado Personal',NULL,0.95),
('cepillo electrico','cepillo electrico','Cuidado Personal',NULL,1.00),
('cepillos electricos','cepillos electricos','Cuidado Personal',NULL,0.95),
('plancha de cabello','plancha de cabello','Cuidado Personal',NULL,1.00),
('planchas de cabello','planchas de cabello','Cuidado Personal',NULL,0.95),
('secador de pelo','secador de pelo','Cuidado Personal',NULL,1.00),
('secadores de pelo','secadores de pelo','Cuidado Personal',NULL,0.95),
('bici','bici','Deportes',NULL,0.80),
('bicicleta','bicicleta','Deportes',NULL,0.90),
('bicicletas','bicicletas','Deportes',NULL,0.99),
('bicis','bicis','Deportes',NULL,0.95),
('mancuerna','mancuerna','Deportes',NULL,1.00),
('mancuernas','mancuernas','Deportes',NULL,0.95),
('pesas','pesas','Deportes',NULL,1.00),
('trotadora','trotadora','Deportes',NULL,1.00),
('trotadoras','trotadoras','Deportes',NULL,0.95),
('camara','camara','Fotografía',NULL,1.00),
('camara fotografica','camara fotografica','Fotografía',NULL,1.00),
('camaras','camaras','Fotografía',NULL,0.90),
('camaras fotograficas','camaras fotograficas','Fotografía',NULL,0.95),
('drone','drone','Fotografía',NULL,0.80),
('gopro','gopro','Fotografía',NULL,1.00),
('consola','consola','Gaming',NULL,1.00),
('joystick','joystick','Gaming',NULL,1.00),
('nintendo','nintendo','Gaming',NULL,1.00),
('playstation','playstation','Gaming',NULL,1.00),
('ps5','ps5','Gaming',NULL,1.00),
('xbox','xbox','Gaming',NULL,1.00),
('amoladora','amoladora','Herramientas',NULL,1.00),
('caja de herramientas','caja de herramientas','Herramientas',NULL,1.00),
('sierra','sierra','Herramientas',NULL,1.00),
('taladro','taladro','Herramientas',NULL,1.00),
('impresora','impresora','Impresión',NULL,1.00),
('juguete','juguete','Juguetería',NULL,1.00),
('juguetes','juguetes','Juguetería',NULL,1.00),
('laptop','laptop','Laptops',NULL,1.00),
('laptops','laptops','Laptops',NULL,0.99),
('macbook','macbook','Laptops',NULL,1.00),
('macbooks','macbooks','Laptops',NULL,0.95),
('notebook','notebook','Laptops',NULL,1.00),
('notebooks','notebooks','Laptops',NULL,0.95),
('portatil','portatil','Laptops',NULL,1.00),
('portatiles','portatiles','Laptops',NULL,0.95),
('ultrabook','ultrabook','Laptops',NULL,1.00),
('ultrabooks','ultrabooks','Laptops',NULL,0.95),
('centro de lavado','centro de lavado','Lavado',NULL,1.00),
('centros de lavado','centros de lavado','Lavado',NULL,0.95),
('lavadora','lavadora','Lavado',NULL,1.00),
('lavadoras','lavadoras','Lavado',NULL,0.99),
('secadora','secadora','Lavado',NULL,1.00),
('secadoras','secadoras','Lavado',NULL,0.95),
('comida mascota','comida mascota','Mascotas',NULL,0.90),
('correa perro','correa perro','Mascotas',NULL,1.00),
('cama','cama','Muebles',NULL,1.00),
('camas','camas','Muebles',NULL,0.95),
('escritorio','escritorio','Muebles',NULL,1.00),
('escritorios','escritorios','Muebles',NULL,0.95),
('mesa','mesa','Muebles',NULL,0.80),
('mesas','mesas','Muebles',NULL,0.95),
('ropero','ropero','Muebles',NULL,1.00),
('roperos','roperos','Muebles',NULL,0.95),
('silla','silla','Muebles',NULL,0.90),
('sillas','sillas','Muebles',NULL,0.95),
('sillon','sillon','Muebles',NULL,1.00),
('sillones','sillones','Muebles',NULL,0.95),
('sofa','sofa','Muebles',NULL,1.00),
('sofas','sofas','Muebles',NULL,0.95),
('aspiradora','aspiradora','Pequeños Electrodomésticos',NULL,1.00),
('aspiradoras','aspiradoras','Pequeños Electrodomésticos',NULL,0.95),
('plancha de ropa','plancha de ropa','Pequeños Electrodomésticos',NULL,1.00),
('planchas de ropa','planchas de ropa','Pequeños Electrodomésticos',NULL,0.95),
('congelador','congelador','Refrigeración',NULL,1.00),
('congeladores','congeladores','Refrigeración',NULL,0.95),
('frigobar','frigobar','Refrigeración',NULL,1.00),
('frigobares','frigobares','Refrigeración',NULL,0.90),
('heladera','heladera','Refrigeración',NULL,1.00),
('heladeras','heladeras','Refrigeración',NULL,0.95),
('nevera','nevera','Refrigeración',NULL,1.00),
('neveras','neveras','Refrigeración',NULL,0.95),
('refrigerador','refrigerador','Refrigeración',NULL,1.00),
('refrigeradores','refrigeradores','Refrigeración',NULL,0.95),
('reloj','reloj','Relojería',NULL,0.90),
('relojes','relojes','Relojería',NULL,0.95),
('alarma','alarma','Seguridad',NULL,1.00),
('alarmas','alarmas','Seguridad',NULL,0.95),
('caja fuerte','caja fuerte','Seguridad',NULL,1.00),
('cajas fuertes','cajas fuertes','Seguridad',NULL,0.95),
('camara seguridad','camara seguridad','Seguridad',NULL,1.00),
('camaras seguridad','camaras seguridad','Seguridad',NULL,0.95),
('reloj inteligente','reloj inteligente','Smartwatch',NULL,1.00),
('relojes inteligentes','relojes inteligentes','Smartwatch',NULL,0.95),
('smartwatch','smartwatch','Smartwatch',NULL,1.00),
('smartwatches','smartwatches','Smartwatch',NULL,0.95),
('ipad','ipad','Tablets',NULL,1.00),
('ipads','ipads','Tablets',NULL,0.95),
('tablet','tablet','Tablets',NULL,1.00),
('tablets','tablets','Tablets',NULL,0.99),
('pantalla','pantalla','Televisores',NULL,0.80),
('pantallas','pantallas','Televisores',NULL,0.90),
('smart tv','smart tv','Televisores',NULL,1.00),
('smart tvs','smart tvs','Televisores',NULL,0.95),
('tele','tele','Televisores',NULL,0.90),
('teles','teles','Televisores',NULL,0.90),
('television','television','Televisores',NULL,1.00),
('televisiones','televisiones','Televisores',NULL,0.95),
('televisor','televisor','Televisores',NULL,1.00),
('televisores','televisores','Televisores',NULL,0.99),
('tv','tv','Televisores',NULL,1.00),
('tvs','tvs','Televisores',NULL,0.95);

-- Seed de relaciones cross-categoria (categoria pedida != catalogo -> sugerir cercana real)
INSERT IGNORE INTO categorias_relacionadas (categoria_origen, categoria_sugerida, subcategoria_sugerida, razon, prioridad) VALUES
('Aire','Climatización','Aire Acondicionado','linea de aire acondicionado',10),
('Airfryer','Pequeños Electrodomésticos','Freidoras','las airfryers estan en freidoras',10),
('Applewatch','Smartwatch','Smartwatch','linea de smartwatches',20),
('Audifonos','Audio','Audífonos','linea de audifonos',10),
('Auriculares','Audio','Audífonos','linea de audifonos',10),
('Auto','Automotriz','Vehículos','no vendemos autos pero si motocicletas y scooters electricos',10),
('Automoviles','Automotriz','Vehículos','no vendemos autos pero si motocicletas y scooters electricos',10),
('Autos','Automotriz','Vehículos','no vendemos autos pero si motocicletas y scooters electricos',10),
('Bici','Deportes','Bicicletas','linea de bicicletas',10),
('Bicicleta','Deportes','Bicicletas','linea de bicicletas',10),
('Calefon','Climatización','Calefones','linea de calefones',10),
('Cama','Muebles','Bases de Cama','bases de cama + colchones + sommiers',10),
('Camara','Fotografía','Cámaras','camaras de fotografia',30),
('Camara','Seguridad','Cámaras de Seguridad','camaras de seguridad',40),
('Camioneta','Automotriz','Vehículos','no tenemos camionetas pero si motocicletas',20),
('Carros','Automotriz','Vehículos','no vendemos carros pero si motocicletas',10),
('Coches','Automotriz','Vehículos','no vendemos coches pero si motocicletas',20),
('Colchon','Muebles','Colchones','linea de colchones',10),
('Computador','Laptops','Notebooks','notebooks / laptops',20),
('Computadora','Laptops','Notebooks','notebooks / laptops',20),
('Freidora','Pequeños Electrodomésticos','Freidoras','linea de freidoras sin aceite',10),
('Galaxy','Celulares','Smartphones','tenemos varios modelos Samsung Galaxy',20),
('Gatos','Mascotas','Mascotas','accesorios para gatos',10),
('Horno','Cocina','Hornos','hornos empotrables y de sobremesa',10),
('Impresora','Impresión','Impresoras','linea de impresoras',10),
('Iphone','Celulares','Smartphones','tenemos smartphones equivalentes',20),
('Licuadora','Pequeños Electrodomésticos','Licuadoras','linea de licuadoras',10),
('Microondas','Cocina','Microondas','linea de microondas empotrables y libres',10),
('Monitor','Computación','Monitores','linea de monitores PC',10),
('Motocicleta','Automotriz','Accesorios Auto','accesorios y repuestos relacionados',50),
('Nevera','Refrigeración','Refrigeradores','linea de refrigeradores',10),
('Nintendo','Gaming','Consolas','linea de consolas Nintendo',10),
('Pantallas','Televisores','Smart TV','todas nuestras pantallas son Smart TV',10),
('Parlante','Audio','Parlantes','linea de parlantes',10),
('PC','Computación','PC Escritorio','PCs de escritorio',10),
('Perfume','Cuidado Personal','Perfumería','linea de perfumeria',10),
('Perros','Mascotas','Mascotas','accesorios para perros',10),
('PlayStation','Gaming','Consolas','linea de consolas PlayStation',10),
('Proyector','Accesorios TV','Proyectores','proyectores estan en accesorios TV',10),
('PS5','Gaming','Consolas','consolas PlayStation',10),
('Refrigerador','Refrigeración','Refrigeradores','linea de refrigeradores',10),
('Reloj','Relojería','Relojes','linea de relojes',10),
('Secador','Cuidado Personal','Secadores','secadores de cabello',10),
('Sofa','Muebles','Muebles','linea de muebles de sala',10),
('Taladro','Herramientas','Taladros','linea de taladros',10),
('Tesla','Automotriz','Vehículos','no vendemos Tesla pero si motocicletas electricas',20),
('Vehiculos','Automotriz','Vehículos','tenemos motocicletas Bajaj Sunra y Huavi',10),
('Ventilador','Climatización','Ventiladores','linea de ventiladores',10),
('Xbox','Gaming','Consolas','linea de consolas Xbox',10),
('Xiaomi','Celulares','Smartphones','tenemos varios modelos Xiaomi',20);

-- Seed extendido: marcas de autos y motos que el catalogo no tiene.
-- El catalogo Dismac solo vende motocicletas Bajaj/Sunra/Huavi, por lo que
-- cualquier marca automotriz fuera de esas rutea a la vertical correcta con
-- una razon humana que el responder usa en el mensaje.
INSERT IGNORE INTO categorias_relacionadas (categoria_origen, categoria_sugerida, subcategoria_sugerida, razon, prioridad) VALUES
('Audi','Automotriz','Vehículos','no vendemos Audi pero si motocicletas electricas',20),
('BMW','Automotriz','Vehículos','no vendemos BMW pero si motocicletas electricas',20),
('Chevrolet','Automotriz','Vehículos','no vendemos Chevrolet pero si motocicletas',20),
('Ducati','Automotriz','Vehículos','ducati es de motos, tenemos motocicletas Bajaj y Sunra',15),
('Ferrari','Automotriz','Vehículos','no vendemos Ferrari pero si motocicletas electricas',20),
('Ford','Automotriz','Vehículos','no vendemos Ford pero si motocicletas',20),
('Honda','Automotriz','Vehículos','no vendemos autos Honda pero si motocicletas',25),
('Hyundai','Automotriz','Vehículos','no vendemos autos Hyundai pero si motocicletas',20),
('Kawasaki','Automotriz','Vehículos','kawasaki es de motos, tenemos motocicletas Bajaj y Sunra',15),
('Kia','Automotriz','Vehículos','no vendemos autos Kia pero si motocicletas',20),
('KTM','Automotriz','Vehículos','KTM es de motos, tenemos motocicletas Bajaj y Sunra',15),
('Lamborghini','Automotriz','Vehículos','no vendemos Lamborghini pero si motocicletas electricas',20),
('Mercedes','Automotriz','Vehículos','no vendemos Mercedes pero si motocicletas electricas',20),
('Nissan','Automotriz','Vehículos','no vendemos Nissan pero si motocicletas electricas',20),
('Porsche','Automotriz','Vehículos','no vendemos Porsche pero si motocicletas electricas',20),
('Suzuki','Automotriz','Vehículos','no vendemos autos Suzuki pero si motocicletas',25),
('Toyota','Automotriz','Vehículos','no vendemos Toyota pero si motocicletas electricas',20),
('Yamaha','Automotriz','Vehículos','yamaha es de motos, tenemos motocicletas Bajaj y Sunra',15);

-- ------------------------------------------------------------
-- Palabras clave por producto (opcional, complementa el FULLTEXT
-- con sinonimos populares que el catalogo no usa literal).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS producto_keywords (
    sku                     VARCHAR(64)  NOT NULL,
    keyword                 VARCHAR(80)  NOT NULL,
    keyword_norm            VARCHAR(80)  NOT NULL,
    fuente                  VARCHAR(40)  NOT NULL DEFAULT 'ingestor',

    PRIMARY KEY (sku, keyword_norm),
    INDEX ix_kw (keyword_norm),
    CONSTRAINT fk_kw_producto FOREIGN KEY (sku) REFERENCES productos(sku)
        ON UPDATE CASCADE ON DELETE CASCADE
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
