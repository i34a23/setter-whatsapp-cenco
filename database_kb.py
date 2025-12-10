import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_kb_db_connection():
    """
    Crea y retorna una conexión a la base de datos de Knowledge Base (Supabase KB)
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('KB_DB_HOST'),
            port=os.getenv('KB_DB_PORT'),
            database=os.getenv('KB_DB_NAME'),
            user=os.getenv('KB_DB_USER'),
            password=os.getenv('KB_DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos KB: {e}")
        return None

def test_kb_connection():
    """
    Prueba la conexión a la base de datos de Knowledge Base
    """
    conn = get_kb_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print(f"Conexión exitosa a PostgreSQL (Knowledge Base)")
            print(f"Versión: {db_version}")
            
            # Verificar que existen las tablas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('knowledge_bases', 'knowledge_points')
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"Tablas encontradas: {[t['table_name'] for t in tables]}")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al ejecutar query: {e}")
            return False
    return False