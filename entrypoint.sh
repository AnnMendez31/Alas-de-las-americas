#!/bin/bash
set -e

echo "==> Esperando que SQL Server este listo..."
until sqlcmd -S "$DB_HOST" -U "$DB_USER" -P "$DB_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1; do
    echo "    SQL Server no disponible, reintentando en 3s..."
    sleep 3
done
echo "==> SQL Server listo."

echo "==> Creando base de datos si no existe..."
sqlcmd -S "$DB_HOST" -U "$DB_USER" -P "$DB_PASSWORD" -C \
    -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'AlasAmericas') CREATE DATABASE AlasAmericas;"

echo "==> Aplicando migraciones Django..."
python manage.py migrate

echo "==> Verificando si la base de datos necesita seed..."
PAIS_COUNT=$(sqlcmd -S "$DB_HOST" -U "$DB_USER" -P "$DB_PASSWORD" -C \
    -d AlasAmericas -h -1 -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM Pais" 2>/dev/null | tr -d ' \r\n')

if [ "$PAIS_COUNT" = "0" ] || [ -z "$PAIS_COUNT" ]; then
    echo "==> Cargando datos iniciales (seed)..."
    sqlcmd -S "$DB_HOST" -U "$DB_USER" -P "$DB_PASSWORD" -C \
        -d AlasAmericas -i /app/SQL_AlasAmericas.sql

    echo "==> Cargando ConfiguracionClase..."
    sqlcmd -S "$DB_HOST" -U "$DB_USER" -P "$DB_PASSWORD" -C -d AlasAmericas -Q "
    SET QUOTED_IDENTIFIER ON; SET ARITHABORT ON;
    DECLARE @i INT = 1;
    WHILE @i <= 38 BEGIN
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@i AND clase_id=1)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 1, 150);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@i AND clase_id=3)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@i, 3, 12);
        SET @i = @i + 1;
    END
    DECLARE @j INT = 39;
    WHILE @j <= 52 BEGIN
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@j AND clase_id=1)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@j, 1, 130);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@j AND clase_id=2)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@j, 2, 20);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@j AND clase_id=3)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@j, 3, 12);
        SET @j = @j + 1;
    END
    DECLARE @k INT = 53;
    WHILE @k <= 58 BEGIN
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@k AND clase_id=1)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@k, 1, 180);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@k AND clase_id=2)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@k, 2, 30);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@k AND clase_id=3)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@k, 3, 20);
        IF NOT EXISTS (SELECT 1 FROM ConfiguracionClase WHERE aeronave_id=@k AND clase_id=4)
            INSERT INTO ConfiguracionClase (aeronave_id, clase_id, cantidad_asientos) VALUES (@k, 4, 8);
        SET @k = @k + 1;
    END"
    echo "==> Seed completado."
else
    echo "==> Base de datos ya tiene datos, omitiendo seed."
fi

echo "==> Iniciando servidor Django en 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
