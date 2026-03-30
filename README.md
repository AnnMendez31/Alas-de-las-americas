# Alas de las Américas

Sistema de gestión de reservas de vuelos.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado y corriendo
-[GIT](https://git-scm.com/) Instalado

## Cómo correr el proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/AnnMendez31/Alas-de-las-americas.git
cd "Alas de las americas"
```

### 2. Crear el archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido:

```
DB_NAME=AlasAmericas
DB_PASSWORD=AlasAmericas@2026!
DB_PORT=
```

### 3. Levantar la aplicación

```bash
docker compose up --build
```

> La primera vez tarda unos minutos porque descarga las imágenes de SQL Server y Python, instala dependencias y carga los datos iniciales automáticamente.

### 4. Abrir en el navegador

Una vez que veas el mensaje `Starting development server at http://0.0.0.0:8000/`, abre:

**http://localhost:8000**

Panel de administración: **http://localhost:8000/admin**

---

## Crear usuario administrador

Con los contenedores corriendo, abre otra terminal y ejecuta:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Comandos útiles

| Comando | Descripción |
|---|---|
| `docker compose up --build` | Iniciar (primera vez o tras cambios) |
| `docker compose up` | Iniciar normalmente |
| `docker compose down` | Detener y eliminar contenedores |
| `docker compose down -v` | Detener y borrar también la base de datos |
| `docker compose logs web` | Ver logs del servidor Django |

---
