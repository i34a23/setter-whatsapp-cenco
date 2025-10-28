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
    
    -- Índices para búsquedas rápidas
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

CREATE TRIGGER update_prospectos_raw_updated_at 
    BEFORE UPDATE ON prospectos_raw 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios
COMMENT ON TABLE prospectos_raw IS 'Tabla para almacenar prospectos importados de diferentes fuentes';
COMMENT ON COLUMN prospectos_raw.datos_adicionales IS 'Columnas adicionales del archivo original en formato JSON';
COMMENT ON COLUMN prospectos_raw.lote_importacion IS 'ID único del lote de importación para poder rastrear y eliminar si es necesario';
