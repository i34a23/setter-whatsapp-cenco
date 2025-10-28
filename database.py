import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """
    Crea y retorna una conexión a la base de datos Supabase
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def test_connection():
    """
    Prueba la conexión a la base de datos
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print(f"Conexión exitosa a PostgreSQL")
            print(f"Versión: {db_version}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al ejecutar query: {e}")
            return False
    return False
