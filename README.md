# WhatsApp Dashboard - Panel de Administración

Dashboard de administración para el Setter de WhatsApp con Flask y Supabase.

## 🚀 Características

- ✅ Flask como framework web
- ✅ Conexión a Supabase (PostgreSQL)
- ✅ Docker y Docker Compose
- ✅ Interfaz web responsive
- ✅ Estructura base lista para expandir

## 📋 Requisitos

- Docker
- Docker Compose

## 🔧 Instalación y Uso

### 1. Clonar o descargar el proyecto

### 2. Configurar variables de entorno

Las credenciales ya están configuradas en `.env`. Si necesitas cambiarlas:

```bash
cp .env.example .env
# Edita .env con tus credenciales
```

### 3. Construir y ejecutar con Docker

```bash
# Construir la imagen
docker-compose build

# Iniciar el contenedor
docker-compose up
```

O en un solo comando:

```bash
docker-compose up --build
```

### 4. Acceder a la aplicación

Abre tu navegador en: `http://localhost:5000`

## 🛠️ Comandos útiles

```bash
# Detener los contenedores
docker-compose down

# Ver logs
docker-compose logs -f

# Reconstruir después de cambios
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
whatsapp-dashboard/
├── app.py                  # Aplicación principal Flask
├── database.py             # Configuración de conexión a BD
├── requirements.txt        # Dependencias Python
├── Dockerfile             # Configuración Docker
├── docker-compose.yml     # Orquestación Docker
├── .env                   # Variables de entorno (no subir a git)
├── .env.example          # Plantilla de variables
├── .gitignore            # Archivos a ignorar en git
├── templates/            
│   └── index.html        # Template principal
├── static/
│   ├── css/
│   │   └── style.css     # Estilos
│   └── js/
│       └── main.js       # JavaScript
└── README.md             # Este archivo
```

## 🔌 Endpoints Disponibles

- `GET /` - Página principal del dashboard
- `GET /health` - Verificar estado de la aplicación
- `GET /db-test` - Probar conexión a la base de datos

## 🔐 Configuración de Base de Datos

La aplicación se conecta a Supabase usando las siguientes variables:

- `DB_HOST`: Host de Supabase
- `DB_PORT`: Puerto (6543)
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña

## 📝 Próximos Pasos

Este es un proyecto base. Puedes agregar:

- [ ] Autenticación de usuarios
- [ ] CRUD para gestionar datos
- [ ] API REST para WhatsApp
- [ ] Panel de métricas y estadísticas
- [ ] Gestión de mensajes
- [ ] Configuración de webhooks

## 🐛 Solución de Problemas

### Error de conexión a la base de datos

Verifica que las credenciales en `.env` sean correctas y que Supabase esté accesible.

### Puerto 5000 ocupado

Cambia el puerto en `docker-compose.yml`:

```yaml
ports:
  - "8000:5000"  # Usar puerto 8000 en lugar de 5000
```

## 📄 Licencia

Proyecto base para desarrollo.
