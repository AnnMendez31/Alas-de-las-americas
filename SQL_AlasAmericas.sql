-- ============================================================
-- SCRIPT 1 - CREAR BASE DE DATOS Y TABLAS
-- Archivo: 01_Crea_BD_Y_Tablas.sql
-- ============================================================

USE master;
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'AlasAmericas')
    CREATE DATABASE AlasAmericas;
GO

USE AlasAmericas;
GO

-- ============================================================
-- BLOQUE 1 — GEOGRAFÍA
-- ============================================================

CREATE TABLE Pais (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    nombre     NVARCHAR(100) NOT NULL,
    codigo_iso NVARCHAR(3)   NOT NULL UNIQUE
);
GO

CREATE TABLE Ciudad (
    id      INT IDENTITY(1,1) PRIMARY KEY,
    nombre  NVARCHAR(100) NOT NULL,
    pais_id INT           NOT NULL,
    CONSTRAINT FK_Ciudad_Pais FOREIGN KEY (pais_id) REFERENCES Pais(id)
);
GO

CREATE TABLE Aeropuerto (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(150) NOT NULL,
    codigo_iata NVARCHAR(3)   NOT NULL UNIQUE,
    ciudad_id   INT           NOT NULL,
    CONSTRAINT FK_Aeropuerto_Ciudad FOREIGN KEY (ciudad_id) REFERENCES Ciudad(id)
);
GO

-- ============================================================
-- BLOQUE 2 — FLOTA DE AERONAVES
-- ============================================================

CREATE TABLE ModeloAeronave (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    nombre           NVARCHAR(100) NOT NULL,
    fabricante       NVARCHAR(100) NOT NULL,
    capacidad_maxima INT           NOT NULL CHECK (capacidad_maxima > 0)
);
GO

CREATE TABLE Aeronave (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    matricula        NVARCHAR(20) NOT NULL UNIQUE,
    modelo_id        INT          NOT NULL,
    anio_fabricacion INT          NOT NULL,
    activa           BIT          NOT NULL DEFAULT 1,
    CONSTRAINT FK_Aeronave_Modelo FOREIGN KEY (modelo_id) REFERENCES ModeloAeronave(id)
);
GO

CREATE TABLE ClaseServicio (
    id     INT IDENTITY(1,1) PRIMARY KEY,
    codigo NVARCHAR(20) NOT NULL UNIQUE
        CHECK (codigo IN ('ECONOMICA','ECONOMICA_PREMIUM','EJECUTIVA','PRIMERA')),
    nombre NVARCHAR(50) NOT NULL
);
GO

CREATE TABLE ConfiguracionClase (
    id                INT IDENTITY(1,1) PRIMARY KEY,
    aeronave_id       INT NOT NULL,
    clase_id          INT NOT NULL,
    cantidad_asientos INT NOT NULL CHECK (cantidad_asientos > 0),
    CONSTRAINT FK_ConfigClase_Aeronave FOREIGN KEY (aeronave_id) REFERENCES Aeronave(id),
    CONSTRAINT FK_ConfigClase_Clase    FOREIGN KEY (clase_id)    REFERENCES ClaseServicio(id),
    CONSTRAINT UQ_ConfigClase          UNIQUE (aeronave_id, clase_id)
);
GO

CREATE TABLE Asiento (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    aeronave_id   INT          NOT NULL,
    clase_id      INT          NOT NULL,
    fila          INT          NOT NULL CHECK (fila > 0),
    letra         NVARCHAR(2)  NOT NULL,
    junto_ventana BIT          NOT NULL DEFAULT 0,
    junto_pasillo BIT          NOT NULL DEFAULT 0,
    estado        NVARCHAR(20) NOT NULL DEFAULT 'OPERATIVO'
        CHECK (estado IN ('OPERATIVO','MANTENIMIENTO')),
    CONSTRAINT FK_Asiento_Aeronave FOREIGN KEY (aeronave_id) REFERENCES Aeronave(id),
    CONSTRAINT FK_Asiento_Clase    FOREIGN KEY (clase_id)    REFERENCES ClaseServicio(id),
    CONSTRAINT UQ_Asiento          UNIQUE (aeronave_id, fila, letra)
);
GO

-- ============================================================
-- BLOQUE 3 — ITINERARIOS Y VUELOS
-- ============================================================

CREATE TABLE PeriodoItinerario (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    codigo      NVARCHAR(10) NOT NULL UNIQUE
        CHECK (codigo IN ('MAR_JUL','JUL_NOV','NOV_MAR')),
    fecha_inicio DATE NOT NULL,
    fecha_fin    DATE NOT NULL
);
GO

CREATE TABLE Itinerario (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    periodo_id       INT          NOT NULL,
    origen_id        INT          NOT NULL,
    destino_id       INT          NOT NULL,
    hora_salida      TIME         NOT NULL,
    hora_llegada     TIME         NOT NULL,
    duracion_minutos INT          NOT NULL CHECK (duracion_minutos > 0),
    dias_operacion   NVARCHAR(50) NOT NULL,
    CONSTRAINT FK_Itinerario_Periodo FOREIGN KEY (periodo_id)  REFERENCES PeriodoItinerario(id),
    CONSTRAINT FK_Itinerario_Origen  FOREIGN KEY (origen_id)   REFERENCES Aeropuerto(id),
    CONSTRAINT FK_Itinerario_Destino FOREIGN KEY (destino_id)  REFERENCES Aeropuerto(id)
);
GO

-- ============================================================
-- TABLA ESCALA — Paradas intermedias de un itinerario
-- Agregada para soportar vuelos con conexiones
-- Relación: Itinerario 1 → N Escala
-- ============================================================

CREATE TABLE Escala (
    id                    INT IDENTITY(1,1) PRIMARY KEY,
    itinerario_id         INT NOT NULL,
    aeropuerto_escala_id  INT NOT NULL,
    orden                 INT NOT NULL CHECK (orden > 0),
    duracion_minutos      INT NOT NULL DEFAULT 60 CHECK (duracion_minutos > 0),
    CONSTRAINT FK_Escala_Itinerario  FOREIGN KEY (itinerario_id)        REFERENCES Itinerario(id)  ON DELETE CASCADE,
    CONSTRAINT FK_Escala_Aeropuerto  FOREIGN KEY (aeropuerto_escala_id) REFERENCES Aeropuerto(id),
    -- Un itinerario no puede tener dos escalas con el mismo orden
    CONSTRAINT UQ_Escala_Orden       UNIQUE (itinerario_id, orden)
);
GO

CREATE TABLE Vuelo (
    id                INT IDENTITY(1,1) PRIMARY KEY,
    numero_vuelo      NVARCHAR(15) NOT NULL UNIQUE,
    itinerario_id     INT          NOT NULL,
    aeronave_id       INT          NOT NULL,
    fecha_salida      DATE         NOT NULL,
    fecha_llegada     DATE         NOT NULL,
    hora_salida_real  TIME         NULL,
    hora_llegada_real TIME         NULL,
    estado            NVARCHAR(20) NOT NULL DEFAULT 'PROGRAMADO'
        CHECK (estado IN ('PROGRAMADO','EMBARCANDO','EN_VUELO','ATERRIZADO','CANCELADO','DEMORADO')),
    CONSTRAINT FK_Vuelo_Itinerario FOREIGN KEY (itinerario_id) REFERENCES Itinerario(id),
    CONSTRAINT FK_Vuelo_Aeronave   FOREIGN KEY (aeronave_id)   REFERENCES Aeronave(id),
    CONSTRAINT UQ_Vuelo            UNIQUE (numero_vuelo, fecha_salida)
);
GO

-- ============================================================
-- BLOQUE 4 — TARIFAS Y EQUIPAJE
-- ============================================================

CREATE TABLE TipoEquipaje (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    nombre      NVARCHAR(50)  NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    es_bodega   BIT           NOT NULL DEFAULT 0
);
GO

CREATE TABLE Tarifa (
    id                         INT           IDENTITY(1,1) PRIMARY KEY,
    vuelo_id                   INT           NOT NULL,
    clase_id                   INT           NOT NULL,
    precio                     DECIMAL(10,2) NOT NULL CHECK (precio >= 0),
    moneda                     NVARCHAR(3)   NOT NULL DEFAULT 'USD',
    seleccion_asiento_incluida BIT           NOT NULL DEFAULT 0,
    cargo_seleccion_asiento    DECIMAL(8,2)  NOT NULL DEFAULT 0.00,
    fecha_actualizacion        DATETIME      NOT NULL DEFAULT GETDATE(),
    disponible                 BIT           NOT NULL DEFAULT 1,
    CONSTRAINT FK_Tarifa_Vuelo FOREIGN KEY (vuelo_id)  REFERENCES Vuelo(id),
    CONSTRAINT FK_Tarifa_Clase FOREIGN KEY (clase_id)  REFERENCES ClaseServicio(id),
    CONSTRAINT UQ_Tarifa       UNIQUE (vuelo_id, clase_id)
);
GO

CREATE TABLE PoliticaEquipaje (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    tarifa_id        INT          NOT NULL,
    tipo_equipaje_id INT          NOT NULL,
    cantidad_maxima  INT          NOT NULL CHECK (cantidad_maxima > 0),
    peso_maximo_kg   DECIMAL(5,2) NOT NULL CHECK (peso_maximo_kg > 0),
    CONSTRAINT FK_PolEq_Tarifa FOREIGN KEY (tarifa_id)        REFERENCES Tarifa(id),
    CONSTRAINT FK_PolEq_Tipo   FOREIGN KEY (tipo_equipaje_id) REFERENCES TipoEquipaje(id),
    CONSTRAINT UQ_PoliticaEquipaje UNIQUE (tarifa_id, tipo_equipaje_id)
);
GO

-- ============================================================
-- BLOQUE 5 — CLIENTES, PASAJEROS Y RESERVAS
-- ============================================================

CREATE TABLE Cliente (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    nombre         NVARCHAR(100) NOT NULL,
    apellido       NVARCHAR(100) NOT NULL,
    email          NVARCHAR(254) NOT NULL UNIQUE,
    telefono       NVARCHAR(20)  NULL,
    fecha_registro DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE Pasajero (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    nombre           NVARCHAR(100) NOT NULL,
    apellido         NVARCHAR(100) NOT NULL,
    fecha_nacimiento DATE          NOT NULL,
    numero_pasaporte NVARCHAR(20)  NOT NULL UNIQUE,
    nacionalidad_id  INT           NOT NULL,
    email            NVARCHAR(254) NULL,
    telefono         NVARCHAR(20)  NULL,
    CONSTRAINT FK_Pasajero_Pais FOREIGN KEY (nacionalidad_id) REFERENCES Pais(id)
);
GO

CREATE TABLE Reserva (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    codigo_reserva NVARCHAR(10)  NOT NULL UNIQUE,
    cliente_id     INT           NOT NULL,
    tipo           NVARCHAR(15)  NOT NULL
        CHECK (tipo IN ('IDA','IDA_VUELTA','MULTIDESTINO')),
    estado         NVARCHAR(15)  NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE','CONFIRMADA','CANCELADA','COMPLETADA')),
    fecha_creacion DATETIME      NOT NULL DEFAULT GETDATE(),
    precio_total   DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    moneda         NVARCHAR(3)   NOT NULL DEFAULT 'USD',
    CONSTRAINT FK_Reserva_Cliente FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
);
GO

CREATE TABLE SegmentoReserva (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    reserva_id  INT NOT NULL,
    vuelo_id    INT NOT NULL,
    tarifa_id   INT NOT NULL,
    pasajero_id INT NOT NULL,
    orden       INT NOT NULL CHECK (orden > 0),
    CONSTRAINT FK_Segmento_Reserva  FOREIGN KEY (reserva_id)  REFERENCES Reserva(id),
    CONSTRAINT FK_Segmento_Vuelo    FOREIGN KEY (vuelo_id)    REFERENCES Vuelo(id),
    CONSTRAINT FK_Segmento_Tarifa   FOREIGN KEY (tarifa_id)   REFERENCES Tarifa(id),
    CONSTRAINT FK_Segmento_Pasajero FOREIGN KEY (pasajero_id) REFERENCES Pasajero(id),
    CONSTRAINT UQ_Segmento          UNIQUE (reserva_id, vuelo_id, pasajero_id)
);
GO

CREATE TABLE AsientoReservado (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    segmento_id     INT          NOT NULL UNIQUE,
    asiento_id      INT          NOT NULL,
    cargo_adicional DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT FK_AsientoRes_Segmento FOREIGN KEY (segmento_id) REFERENCES SegmentoReserva(id),
    CONSTRAINT FK_AsientoRes_Asiento  FOREIGN KEY (asiento_id)  REFERENCES Asiento(id),
    CONSTRAINT UQ_AsientoReservado    UNIQUE (segmento_id, asiento_id)
);
GO

CREATE TABLE EquipajeReserva (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    segmento_id      INT          NOT NULL,
    pasajero_id      INT          NOT NULL,
    tipo_equipaje_id INT          NOT NULL,
    cantidad         INT          NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    peso_kg          DECIMAL(5,2) NOT NULL CHECK (peso_kg > 0),
    cargo_adicional  DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT FK_EqRes_Segmento FOREIGN KEY (segmento_id)      REFERENCES SegmentoReserva(id),
    CONSTRAINT FK_EqRes_Pasajero FOREIGN KEY (pasajero_id)      REFERENCES Pasajero(id),
    CONSTRAINT FK_EqRes_TipoEq   FOREIGN KEY (tipo_equipaje_id) REFERENCES TipoEquipaje(id)
);
GO

PRINT '✅ Tablas creadas exitosamente (incluyendo Escala).';
GO

-- ============================================================
-- SCRIPT 2 - CARGAR DATOS BÁSICOS
-- Archivo: 02_Inserta_Datos_Basicos.sql
-- ============================================================

USE AlasAmericas;
GO

-- ============================================================
-- DATOS — PAÍSES, CIUDADES Y AEROPUERTOS
-- ============================================================

INSERT INTO Pais (nombre, codigo_iso) VALUES
('República Dominicana', 'REP'),
('Estados Unidos',       'EST'),
('Canadá',               'CAN'),
('Jamaica',              'JAM'),
('Haití',                'HAI'),
('México',               'MEX'),
('Colombia',             'COL'),
('Perú',                 'PER'),
('Ecuador',              'ECU'),
('Brasil',               'BRA'),
('Argentina',            'ARG'),
('Chile',                'CHI'),
('Uruguay',              'URU'),
('Paraguay',             'PAR'),
('San Martín',           'SAN'),
('Aruba',                'ARU'),
('Curazao',              'CUR'),
('Guatemala',            'GUA'),
('Costa Rica',           'COS'),
('Panamá',               'PAN');

PRINT '✅ 20 países insertados.';
GO

INSERT INTO Ciudad (nombre, pais_id) VALUES
('Santiago',         1), ('Santo Domingo',   1), ('Punta Cana',    1), ('Puerto Plata',  1),
('Miami',            2), ('Orlando',         2), ('New York',      2), ('Boston',        2), ('Chicago',  2),
('Montreal',         3), ('Toronto',         3),
('Kingston',         4),
('Puerto Príncipe',  5),
('Ciudad de México', 6), ('Cancún',          6),
('Bogotá',           7), ('Cartagena',       7), ('Medellín',      7),
('Lima',             8),
('Quito',            9),
('São Paulo',       10), ('Río de Janeiro', 10),
('Buenos Aires',    11), ('Rosario',        11), ('Córdoba',      11), ('Mendoza',      11),
('Santiago',        12), ('Antofagasta',    12), ('Punta Arenas', 12),
('Montevideo',      13),
('Asunción',        14),
('San Martín',      15),
('Aruba',           16),
('Curazao',         17),
('Guatemala',       18),
('San José',        19),
('Panamá',          20);

PRINT '✅ 37 ciudades insertadas.';
GO

INSERT INTO Aeropuerto (nombre, codigo_iata, ciudad_id) VALUES
('Aeropuerto Int. de Santiago',          'STI',  1),
('Aeropuerto Int. de Santo Domingo',     'SDQ',  2),
('Aeropuerto Int. de Punta Cana',        'PUJ',  3),
('Aeropuerto Int. de Puerto Plata',      'POP',  4),
('Aeropuerto Int. de Miami',             'MIA',  5),
('Aeropuerto Int. de Orlando',           'MCO',  6),
('Aeropuerto Int. de New York',          'JFK',  7),
('Aeropuerto Int. de Boston',            'BOS',  8),
('Aeropuerto Int. de Chicago',           'ORD',  9),
('Aeropuerto Int. de Montreal',          'YUL', 10),
('Aeropuerto Int. de Toronto',           'YYZ', 11),
('Aeropuerto Int. de Kingston',          'KIN', 12),
('Aeropuerto Int. de Puerto Príncipe',   'PAP', 13),
('Aeropuerto Int. de Ciudad de México',  'MEX', 14),
('Aeropuerto Int. de Cancún',            'CUN', 15),
('Aeropuerto Int. de Bogotá',            'BOG', 16),
('Aeropuerto Int. de Cartagena',         'CTG', 17),
('Aeropuerto Int. de Medellín',          'MDE', 18),
('Aeropuerto Int. de Lima',              'LIM', 19),
('Aeropuerto Int. de Quito',             'UIO', 20),
('Aeropuerto Int. de São Paulo',         'GRU', 21),
('Aeropuerto Int. de Río de Janeiro',    'GIG', 22),
('Aeropuerto Int. de Buenos Aires',      'EZE', 23),
('Aeropuerto Int. de Rosario',           'ROS', 24),
('Aeropuerto Int. de Córdoba',           'COR', 25),
('Aeropuerto Int. de Mendoza',           'MDZ', 26),
('Aeropuerto Int. de Santiago Chile',    'SCL', 27),
('Aeropuerto Int. de Antofagasta',       'ANF', 28),
('Aeropuerto Int. de Punta Arenas',      'PUQ', 29),
('Aeropuerto Int. de Montevideo',        'MVD', 30),
('Aeropuerto Int. de Asunción',          'ASU', 31),
('Aeropuerto Int. de San Martín',        'SXM', 32),
('Aeropuerto Int. de Aruba',             'AUA', 33),
('Aeropuerto Int. de Curazao',           'CUR', 34),
('Aeropuerto Int. de Guatemala',         'GUA', 35),
('Aeropuerto Int. de San José',          'SJO', 36),
('Aeropuerto Int. de Panamá',            'PTY', 37);

PRINT '✅ 37 aeropuertos insertados.';
GO

-- ============================================================
-- CLASES DE SERVICIO
-- ============================================================

INSERT INTO ClaseServicio (codigo, nombre) VALUES
('ECONOMICA',         'Económica'),
('ECONOMICA_PREMIUM', 'Económica Premium'),
('EJECUTIVA',         'Ejecutiva (Business)'),
('PRIMERA',           'Primera Clase');

PRINT '✅ 4 clases de servicio insertadas.';
GO

-- ============================================================
-- MODELOS DE AERONAVE Y FLOTA
-- ============================================================

INSERT INTO ModeloAeronave (nombre, fabricante, capacidad_maxima) VALUES
('Airbus A320',      'Airbus', 180),
('Boeing 737 MAX 8', 'Boeing', 170),
('Boeing 787',       'Boeing', 250);

PRINT '✅ 3 modelos de aeronave insertados.';
GO

-- Airbus A320 (modelo_id=1) — 38 unidades
INSERT INTO Aeronave (matricula, modelo_id, anio_fabricacion, activa) VALUES
('HI-AA320001',1,2022,1),('HI-AA320002',1,2022,1),('HI-AA320003',1,2022,1),('HI-AA320004',1,2022,1),
('HI-AA320005',1,2022,1),('HI-AA320006',1,2022,1),('HI-AA320007',1,2022,1),('HI-AA320008',1,2022,1),
('HI-AA320009',1,2022,1),('HI-AA320010',1,2022,1),('HI-AA320011',1,2022,1),('HI-AA320012',1,2022,1),
('HI-AA320013',1,2022,1),('HI-AA320014',1,2022,1),('HI-AA320015',1,2022,1),('HI-AA320016',1,2022,1),
('HI-AA320017',1,2022,1),('HI-AA320018',1,2022,1),('HI-AA320019',1,2022,1),('HI-AA320020',1,2022,1),
('HI-AA320021',1,2022,1),('HI-AA320022',1,2022,1),('HI-AA320023',1,2022,1),('HI-AA320024',1,2022,1),
('HI-AA320025',1,2022,1),('HI-AA320026',1,2022,1),('HI-AA320027',1,2022,1),('HI-AA320028',1,2022,1),
('HI-AA320029',1,2022,1),('HI-AA320030',1,2022,1),('HI-AA320031',1,2022,1),('HI-AA320032',1,2022,1),
('HI-AA320033',1,2022,1),('HI-AA320034',1,2022,1),('HI-AA320035',1,2022,1),('HI-AA320036',1,2022,1),
('HI-AA320037',1,2022,1),('HI-AA320038',1,2022,1);

PRINT '✅ 38 Airbus A320 insertados.';
GO

-- Boeing 737 MAX 8 (modelo_id=2) — 14 unidades
INSERT INTO Aeronave (matricula, modelo_id, anio_fabricacion, activa) VALUES
('HI-B737001',2,2022,1),('HI-B737002',2,2022,1),('HI-B737003',2,2022,1),('HI-B737004',2,2022,1),
('HI-B737005',2,2022,1),('HI-B737006',2,2022,1),('HI-B737007',2,2022,1),('HI-B737008',2,2022,1),
('HI-B737009',2,2022,1),('HI-B737010',2,2022,1),('HI-B737011',2,2022,1),('HI-B737012',2,2022,1),
('HI-B737013',2,2022,1),('HI-B737014',2,2022,1);

PRINT '✅ 14 Boeing 737 MAX 8 insertados.';
GO

-- Boeing 787 (modelo_id=3) — 6 unidades
INSERT INTO Aeronave (matricula, modelo_id, anio_fabricacion, activa) VALUES
('HI-B787001',3,2022,1),('HI-B787002',3,2022,1),('HI-B787003',3,2022,1),
('HI-B787004',3,2022,1),('HI-B787005',3,2022,1),('HI-B787006',3,2022,1);

PRINT '✅ 6 Boeing 787 insertados.';
GO

-- ============================================================
-- DATOS — PERIODOS DE ITINERARIO Y EQUIPAJE
-- ============================================================

INSERT INTO PeriodoItinerario (codigo, fecha_inicio, fecha_fin) VALUES
('MAR_JUL', '2026-03-01', '2026-07-31'),
('JUL_NOV', '2026-07-01', '2026-11-30'),
('NOV_MAR', '2025-11-01', '2026-03-31');

PRINT '✅ 3 períodos de itinerario insertados.';
GO

INSERT INTO TipoEquipaje (nombre, descripcion, es_bodega) VALUES
('Equipaje de mano',   'Artículo personal + bolso de cabina hasta 10 kg', 0),
('Equipaje de bodega', 'Maleta despachada, máximo 23 kg',                  1),
('Equipaje extra',     'Pieza adicional de bodega',                        1),
('Equipaje deportivo', 'Bicicleta, tabla de surf u equipo especial',       1);

PRINT '✅ 4 tipos de equipaje insertados.';
GO

PRINT '';
PRINT '✅ DATOS BÁSICOS CARGADOS EXITOSAMENTE';
GO

-- ============================================================
-- SCRIPT 3 - CONFIGURACIÓN DE CLASES POR AERONAVE
-- Archivo: 03_Configura_Clases_Aeronaves.sql
-- ============================================================

USE AlasAmericas;
GO

PRINT 'Configurando clases para Airbus A320 (1-38)...';
GO

-- A320 (aeronave_id 1–38)
DECLARE @i INT = 1;
WHILE @i <= 38
BEGIN
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 1, 150);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 3,  12);
    SET @i = @i + 1;
END

PRINT '✅ Airbus A320: 38 aeronaves configuradas';
GO

PRINT 'Configurando clases para Boeing 737 MAX 8 (39-52)...';
GO

-- 737 MAX 8 (aeronave_id 39–52)
DECLARE @i INT = 39;
WHILE @i <= 52
BEGIN
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 1, 130);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 2,  20);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 3,  12);
    SET @i = @i + 1;
END

PRINT '✅ Boeing 737 MAX 8: 14 aeronaves configuradas';
GO

PRINT 'Configurando clases para Boeing 787 (53-58)...';
GO

-- Boeing 787 (aeronave_id 53–58)
DECLARE @i INT = 53;
WHILE @i <= 58
BEGIN
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 1, 180);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 2,  30);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 3,  20);
    INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 4,   8);
    SET @i = @i + 1;
END

PRINT '✅ Boeing 787: 6 aeronaves configuradas';
GO

PRINT '';
PRINT '✅ CONFIGURACIÓN DE CLASES COMPLETADA';
GO

-- ============================================================
-- SCRIPT 4 - PROCEDIMIENTOS ALMACENADOS
-- Archivo: 04_Create_Procedures.sql
-- Descripción: Creación del motor de generación de asientos.
-- ============================================================

USE AlasAmericas;
GO

SET QUOTED_IDENTIFIER ON;
SET ARITHABORT ON;
GO

PRINT '====================================================';
PRINT 'CREANDO PROCEDIMIENTOS ALMACENADOS';
PRINT '====================================================';
PRINT '';

-- ============================================================
-- BLOQUE 1 — PROCEDIMIENTO: sp_GenerarAsientos
-- ============================================================

PRINT 'Creando procedimiento sp_GenerarAsientos...';
GO

-- Primero lo borramos si existe para evitar conflictos de creación
IF OBJECT_ID('dbo.sp_GenerarAsientos', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_GenerarAsientos;
GO

CREATE PROCEDURE dbo.sp_GenerarAsientos
    @AeronaveID INT,
    @ClaseID    INT,
    @Cantidad    INT,
    @FilaInicio INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Variables de control para el ciclo de generación
    DECLARE @Generados INT = 0;
    DECLARE @FilaActual INT = @FilaInicio;
    DECLARE @Letra CHAR(1);
    
    -- Definición de la distribución de letras por fila (Configuración estándar 3-3)
    DECLARE @Letras TABLE (Idx INT, Letra CHAR(1));
    INSERT INTO @Letras VALUES (1,'A'), (2,'B'), (3,'C'), (4,'D'), (5,'E'), (6,'F');

    -- Ciclo Principal: Ejecuta hasta completar la cantidad total de asientos pedida
    WHILE @Generados < @Cantidad
    BEGIN
        DECLARE @i INT = 1;

        -- Ciclo Secundario: Recorre cada una de las 6 letras (asientos) de la fila
        WHILE @i <= 6 AND @Generados < @Cantidad
        BEGIN
            SELECT @Letra = Letra FROM @Letras WHERE Idx = @i;
            
            -- Lógica de seguridad: Solo inserta si el asiento no existe (evita duplicados)
            IF NOT EXISTS (
                SELECT 1 FROM Asiento 
                WHERE aeronave_id = @AeronaveID 
                  AND fila = @FilaActual 
                  AND letra = @Letra
            )
            BEGIN
                INSERT INTO Asiento (
                    aeronave_id, 
                    clase_id, 
                    fila, 
                    letra, 
                    junto_ventana, 
                    junto_pasillo, 
                    estado
                )
                VALUES (
                    @AeronaveID, 
                    @ClaseID, 
                    @FilaActual, 
                    @Letra,
                    -- A y F son ventanas, C y D son pasillos
                    CASE WHEN @Letra IN ('A', 'F') THEN 1 ELSE 0 END,
                    CASE WHEN @Letra IN ('C', 'D') THEN 1 ELSE 0 END,
                    'OPERATIVO'
                );
            END
            
            -- Incrementos: Avanzamos el contador de asientos y el índice de letras
            SET @Generados = @Generados + 1;
            SET @i = @i + 1;
        END

        -- Avanzamos a la siguiente fila numérica
        SET @FilaActual = @FilaActual + 1;
    END
END;
GO

PRINT '✅ Procedimiento sp_GenerarAsientos creado exitosamente.';
PRINT '';
GO

-- ============================================================
-- SCRIPT 5 - GENERAR ASIENTOS (VERSIÓN DINÁMICA)
-- Archivo: 05_Genera_Asientos.sql
-- ============================================================
USE AlasAmericas;
GO

DECLARE @AeronaveID INT, @ClaseEco INT, @ClasePre INT, @ClaseEje INT, @ClasePri INT;

-- 1. Mapeamos los IDs de las clases para no adivinar números
SELECT @ClaseEco = id FROM ClaseServicio WHERE codigo = 'ECONOMICA';
SELECT @ClasePre = id FROM ClaseServicio WHERE codigo = 'ECONOMICA_PREMIUM';
SELECT @ClaseEje = id FROM ClaseServicio WHERE codigo = 'EJECUTIVA';
SELECT @ClasePri = id FROM ClaseServicio WHERE codigo = 'PRIMERA';

PRINT 'Generando asientos por modelo...';

-- 2. AIRBUS A320
DECLARE cur_a320 CURSOR FOR 
    SELECT a.id FROM Aeronave a JOIN ModeloAeronave m ON a.modelo_id = m.id WHERE m.nombre = 'Airbus A320';
OPEN cur_a320; FETCH NEXT FROM cur_a320 INTO @AeronaveID;
WHILE @@FETCH_STATUS = 0 BEGIN
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEco, 150, 1;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEje, 12, 26;
    FETCH NEXT FROM cur_a320 INTO @AeronaveID;
END; CLOSE cur_a320; DEALLOCATE cur_a320;

-- 3. BOEING 737 MAX 8
DECLARE cur_737 CURSOR FOR 
    SELECT a.id FROM Aeronave a JOIN ModeloAeronave m ON a.modelo_id = m.id WHERE m.nombre = 'Boeing 737 MAX 8';
OPEN cur_737; FETCH NEXT FROM cur_737 INTO @AeronaveID;
WHILE @@FETCH_STATUS = 0 BEGIN
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEco, 130, 1;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClasePre, 20, 23;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEje, 12, 27;
    FETCH NEXT FROM cur_737 INTO @AeronaveID;
END; CLOSE cur_737; DEALLOCATE cur_737;

-- 4. BOEING 787
DECLARE cur_787 CURSOR FOR 
    SELECT a.id FROM Aeronave a JOIN ModeloAeronave m ON a.modelo_id = m.id WHERE m.nombre = 'Boeing 787';
OPEN cur_787; FETCH NEXT FROM cur_787 INTO @AeronaveID;
WHILE @@FETCH_STATUS = 0 BEGIN
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEco, 180, 1;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClasePre, 30, 31;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClaseEje, 20, 36;
    EXEC dbo.sp_GenerarAsientos @AeronaveID, @ClasePri, 8, 40;
    FETCH NEXT FROM cur_787 INTO @AeronaveID;
END; CLOSE cur_787; DEALLOCATE cur_787;

PRINT '✅ GENERACIÓN COMPLETADA.';
-- Verificación rápida
SELECT m.nombre, COUNT(*) as TotalAsientos 
FROM Asiento ash
JOIN Aeronave a ON ash.aeronave_id = a.id
JOIN ModeloAeronave m ON a.modelo_id = m.id
GROUP BY m.nombre;
GO

-- ============================================================
-- SCRIPT 6 - VERIFICACIÓN FINAL (OPTIMIZADO)
-- Archivo: 06_Verificacion.sql
-- ============================================================
USE AlasAmericas;
GO

PRINT '====================================================';
PRINT 'VERIFICACIÓN FINAL DE LA BASE DE DATOS';
PRINT '====================================================';
PRINT '';

-- ============================================================
-- Estadísticas de Asientos (Optimizado)
-- ============================================================
PRINT 'ESTADÍSTICAS DE ASIENTOS';
PRINT '----------------------------------------------------';
SELECT 
    m.nombre AS modelo,
    COUNT(DISTINCT a.id) AS aeronaves,
    COUNT(s.id) AS total_asientos
FROM ModeloAeronave m
JOIN Aeronave a ON a.modelo_id = m.id
LEFT JOIN Asiento s ON s.aeronave_id = a.id
GROUP BY m.nombre
ORDER BY m.nombre;
GO

-- ============================================================
-- Estadísticas de Configuración
-- ============================================================
PRINT 'ESTADÍSTICAS DE CONFIGURACIÓN';
PRINT '----------------------------------------------------';
SELECT 
    cs.nombre AS clase,
    COUNT(DISTINCT cc.aeronave_id) AS aeronaves,
    SUM(cc.cantidad_asientos) AS asientos_totales,
    AVG(cc.cantidad_asientos) AS promedio_por_aeronave
FROM ConfiguracionClase cc
JOIN ClaseServicio cs ON cc.clase_id = cs.id
GROUP BY cs.id, cs.nombre
ORDER BY cs.id;
GO

-- ============================================================
-- Estadísticas Generales (CORREGIDO - SIN CROSS JOIN)
-- ============================================================
PRINT 'ESTADÍSTICAS GENERALES';
PRINT '----------------------------------------------------';
-- Usamos subconsultas simples para obtener totales rápidos
SELECT 
    (SELECT COUNT(*) FROM Aeronave) AS total_aeronaves,
    (SELECT COUNT(*) FROM ModeloAeronave) AS total_modelos,
    (SELECT COUNT(*) FROM Asiento) AS total_asientos,
    (SELECT COUNT(*) FROM Ciudad) AS total_ciudades,
    (SELECT COUNT(*) FROM Pais) AS total_paises,
    (SELECT COUNT(*) FROM Aeropuerto) AS total_aeropuertos;
GO

PRINT '';
PRINT '====================================================';
PRINT '✅ BASE DE DATOS ALASAMERICAS LISTA PARA USAR';
PRINT '====================================================';
GO