#!/usr/bin/env python3
"""
Script para inicializar la base de datos
Crea la tabla prospectos_raw si no existe
"""

from database import get_db_connection
import sys

SQL_SCHEMA = """
-- Tabla para almacenar prospectos RAW
CREATE TABLE IF NOT EXISTS prospectos_raw (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    apellidos VARCHAR(255),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    propietario VARCHAR(255),
    canal VARCHAR(255),
    referrer TEXT,
    email_1 VARCHAR(255),
    email_2 VARCHAR(255),
    telefono_1 VARCHAR(50),
    telefono_2 VARCHAR(50),
    programa VARCHAR(255),
    rut VARCHAR(50),
    carrera_postula VARCHAR(255),
    experiencia VARCHAR(255),
    urgencia VARCHAR(255),
    
    -- Metadata
    archivo_origen VARCHAR(500),
    fecha_importacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    lote_importacion VARCHAR(100),
    
    -- Datos adicionales en formato JSON
    datos_adicionales JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_nombre ON prospectos_raw(nombre);
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_email_1 ON prospectos_raw(email_1);
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_telefono_1 ON prospectos_raw(telefono_1);
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_rut ON prospectos_raw(rut);
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_fecha_creacion ON prospectos_raw(fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_prospectos_raw_lote ON prospectos_raw(lote_importacion);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_prospectos_raw_updated_at ON prospectos_raw;
CREATE TRIGGER update_prospectos_raw_updated_at 
    BEFORE UPDATE ON prospectos_raw 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
"""

def init_database():
    """Inicializa la base de datos creando las tablas necesarias"""
    print("=" * 60)
    print("Inicializando Base de Datos")
    print("=" * 60)
    
    try:
        print("\n1. Conectando a la base de datos...")
        conn = get_db_connection()
        
        if not conn:
            print("❌ Error: No se pudo conectar a la base de datos")
            print("\nVerifica:")
            print("  - Las credenciales en el archivo .env")
            print("  - Que Supabase esté accesible")
            print("  - La configuración de red")
            return False
        
        print("✓ Conexión exitosa")
        
        print("\n2. Creando tabla prospectos_raw...")
        cursor = conn.cursor()
        
        # Ejecutar el schema
        cursor.execute(SQL_SCHEMA)
        conn.commit()
        
        print("✓ Tabla creada exitosamente")
        
        # Verificar que la tabla existe
        print("\n3. Verificando tabla...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'prospectos_raw'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ Tabla prospectos_raw verificada")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM prospectos_raw")
            count = cursor.fetchone()[0]
            print(f"\n📊 Registros existentes: {count}")
        else:
            print("❌ Error: La tabla no se creó correctamente")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Inicialización completada exitosamente")
        print("=" * 60)
        print("\nAhora puedes:")
        print("  1. Acceder al dashboard: http://localhost:5000")
        print("  2. Ir a Prospectos RAW")
        print("  3. Subir tu primera lista")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la inicialización:")
        print(f"   {str(e)}")
        print("\nSoluciones posibles:")
        print("  - Verifica que las credenciales en .env sean correctas")
        print("  - Asegúrate de tener acceso a Supabase")
        print("  - Revisa los logs de Docker: docker-compose logs")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
