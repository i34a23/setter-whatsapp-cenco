from flask import Blueprint, render_template, jsonify, request, session
from werkzeug.utils import secure_filename
from database import get_db_connection
from utils.file_processor import FileProcessor
import os
import uuid
from datetime import datetime
import json
import re

prospectos_bp = Blueprint('prospectos', __name__)

UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Campos objetivo y sus sinónimos para mapeo automático
TARGET_FIELDS = {
    'nombre': ['nombre', 'name', 'first_name', 'primer nombre'],
    'apellidos': ['apellidos', 'apellido', 'last_name', 'surname'],
    'fecha_creacion': ['fecha_creacion', 'creado', 'fecha', 'created', 'created_at', 'date'],
    'propietario': ['propietario', 'owner', 'responsable', 'agente'],
    'canal': ['canal', 'channel', 'medium', 'medio'],
    'referrer': ['referrer', 'referencia', 'fuente'],
    'email_1': ['email 1', 'email', 'correo', 'mail', 'e-mail', 'email_1'],
    'email_2': ['email 2', 'email secundario', 'correo 2', 'email_2'],
    'telefono_1': ['telefono 1', 'teléfono 1', 'telefono', 'phone', 'celular', 'movil'],
    'telefono_2': ['telefono 2', 'teléfono 2', 'telefono secundario', 'phone 2'],
    'programa': ['programa', 'programa de estudios', 'course', 'curso'],
    'rut': ['rut', 'dni', 'identification', 'cedula'],
    'carrera_postula': ['carrera a la que postula', 'carrera', 'carrera_postula', 'career'],
    'experiencia': ['experiencia', 'experiencia laboral', 'años de experiencia', 'cuantos años tienes de experiencia laboral'],
    'urgencia': ['urgencia', 'con que urgencia', '¿con que urgencia quieres matricularte?']
}

def normalize_phone(phone):
    """Normaliza teléfono a formato 569XXXXXXXX"""
    if not phone:
        return None
    
    phone_str = str(phone).strip()
    phone_clean = re.sub(r'[^0-9]', '', phone_str)
    
    if phone_clean.startswith('56'):
        phone_clean = phone_clean[2:]
    
    if phone_clean.startswith('9') and len(phone_clean) == 9:
        return '56' + phone_clean
    
    if len(phone_clean) == 8:
        return '569' + phone_clean
    
    return None

@prospectos_bp.route('/')
@prospectos_bp.route('/raw')
def prospectos_raw():
    """Vista principal de prospectos RAW"""
    return render_template('modules/prospectos_raw.html', current_module='prospectos')

@prospectos_bp.route('/api/list')
def list_prospectos():
    """API para listar prospectos con paginación y filtros"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        # Ordenamiento
        sort_column = request.args.get('sort_column', 'created_at')
        sort_order = request.args.get('sort_order', 'DESC')
        
        # Validar columnas permitidas para ordenar
        valid_sort_columns = ['nombre', 'apellidos', 'email_1', 'telefono_1', 
                             'programa', 'propietario', 'fecha_creacion', 'created_at']
        if sort_column not in valid_sort_columns:
            sort_column = 'created_at'
        
        # Validar orden
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        # Filtros
        filters = {}
        for key in ['nombre', 'apellidos', 'email_1', 'telefono_1', 'programa', 'propietario']:
            value = request.args.get(key)
            if value:
                try:
                    filters[key] = json.loads(value)
                except:
                    filters[key] = value
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'prospectos_raw'
            );
        """)
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'data': [],
                'total': 0,
                'page': 1,
                'total_pages': 0
            })
        
        where_clauses = []
        params = []
        
        # FILTRO: Excluir prospectos que ya fueron activados (que existen en leads)
        where_clauses.append("""
            NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
            )
        """)
        
        for column, value in filters.items():
            if isinstance(value, list):
                if None in value:
                    value_list = [v for v in value if v is not None]
                    if value_list:
                        placeholders = ','.join(['%s'] * len(value_list))
                        where_clauses.append(f"({column} IN ({placeholders}) OR {column} IS NULL)")
                        params.extend(value_list)
                    else:
                        where_clauses.append(f"{column} IS NULL")
                else:
                    placeholders = ','.join(['%s'] * len(value))
                    where_clauses.append(f"{column} IN ({placeholders})")
                    params.extend(value)
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        cursor.execute(f"SELECT COUNT(*) as total FROM prospectos_raw WHERE {where_sql}", params)
        total = cursor.fetchone()['total']
        
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Query con ordenamiento
        query = f"""
            SELECT id, nombre, apellidos, email_1, telefono_1, 
                   fecha_creacion, propietario, programa
            FROM prospectos_raw 
            WHERE {where_sql}
            ORDER BY {sort_column} {sort_order}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [page_size, offset])
        
        prospectos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': prospectos,
            'total': total,
            'page': page,
            'total_pages': total_pages,
            'sort_column': sort_column,
            'sort_order': sort_order
        })
    except Exception as e:
        print(f"Error in list_prospectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'data': [],
            'total': 0,
            'page': 1,
            'total_pages': 0
        })


@prospectos_bp.route('/api/column-values')
def get_column_values():
    """Obtiene valores únicos de una columna para filtros"""
    try:
        column = request.args.get('column')
        if not column:
            return jsonify({'success': False, 'error': 'Column required'}), 400
        
        valid_columns = ['nombre', 'apellidos', 'email_1', 'telefono_1', 'programa', 'propietario']
        if column not in valid_columns:
            return jsonify({'success': False, 'error': 'Invalid column'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        query = f"""
            SELECT DISTINCT {column} as value
            FROM prospectos_raw
            WHERE {column} IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
              )
            ORDER BY {column}
            LIMIT 500
        """
        cursor.execute(query)
        
        results = cursor.fetchall()
        values = [row['value'] for row in results]
        
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM prospectos_raw 
            WHERE {column} IS NULL
              AND NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
              )
        """)
        null_count = cursor.fetchone()['count']
        if null_count > 0:
            values.append(None)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'values': values
        })
        
    except Exception as e:
        print(f"Error in get_column_values: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@prospectos_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Endpoint para subir archivo y obtener vista previa"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not FileProcessor.allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': 'Formato no permitido. Use CSV, XLSX o XLS'
            }), 400
        
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        file.save(filepath)
        
        session['upload_file'] = filepath
        session['upload_filename'] = filename
        session['upload_id'] = file_id
        
        preview = FileProcessor.get_preview(filepath, rows=5)
        suggested_mapping = FileProcessor.suggest_mapping(
            preview['columns'], 
            TARGET_FIELDS
        )
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'preview': preview,
            'suggested_mapping': suggested_mapping,
            'target_fields': list(TARGET_FIELDS.keys())
        })
    
    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@prospectos_bp.route('/api/import', methods=['POST'])
def import_data():
    """Endpoint para importar datos con el mapeo confirmado"""
    try:
        data = request.get_json()
        column_mapping = data.get('mapping', {})
        
        if 'upload_file' not in session:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        filepath = session['upload_file']
        filename = session.get('upload_filename', 'unknown')
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        mapped_data = FileProcessor.process_and_map(filepath, column_mapping)
        lote_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session.get('upload_id', 'unknown')}"
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        inserted_count = 0
        
        for record in mapped_data:
            try:
                record['archivo_origen'] = filename
                record['lote_importacion'] = lote_id
                datos_adicionales = record.pop('datos_adicionales', None)
                
                columns = []
                values = []
                
                for key, value in record.items():
                    if key and value is not None:
                        columns.append(key)
                        values.append(value)
                
                if datos_adicionales:
                    columns.append('datos_adicionales')
                    values.append(json.dumps(datos_adicionales))
                
                if not columns:
                    continue
                
                placeholders = ', '.join(['%s'] * len(values))
                columns_str = ', '.join(columns)
                
                query = f"INSERT INTO prospectos_raw ({columns_str}) VALUES ({placeholders})"
                cursor.execute(query, values)
                inserted_count += 1
                
            except Exception as e:
                print(f"Error en fila: {str(e)}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        try:
            os.remove(filepath)
        except:
            pass
        
        session.pop('upload_file', None)
        session.pop('upload_filename', None)
        session.pop('upload_id', None)
        
        return jsonify({
            'success': True,
            'message': f'Se importaron {inserted_count} registros exitosamente',
            'lote_id': lote_id,
            'imported_count': inserted_count
        })
    
    except Exception as e:
        print(f"Error en import_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@prospectos_bp.route('/api/activar', methods=['POST'])
def activar_prospectos():
    """Activa prospectos seleccionados y los pasa a la tabla leads"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': 'No IDs provided'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Obtener prospectos
        placeholders = ','.join(['%s'] * len(ids))
        query = f"""
            SELECT id, nombre, apellidos, email_1, telefono_1, programa, 
                   propietario, carrera_postula, experiencia, urgencia, canal
            FROM prospectos_raw
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, ids)
        prospectos = cursor.fetchall()
        
        activated = 0
        skipped = 0
        errors = []
        
        for prospecto in prospectos:
            # Normalizar teléfono
            session_id = normalize_phone(prospecto['telefono_1'])
            
            if not session_id:
                skipped += 1
                errors.append(f"ID {prospecto['id']}: teléfono inválido")
                print(f"⚠️ Prospecto ID {prospecto['id']} teléfono inválido: '{prospecto['telefono_1']}'")
                continue
            
            print(f"✓ Normalizando: {prospecto['telefono_1']} → {session_id}")
            
            try:
                # Mapear experiencia a integer si es posible
                experiencia_int = None
                if prospecto['experiencia']:
                    try:
                        # Intentar extraer número de la experiencia
                        exp_str = str(prospecto['experiencia'])
                        exp_num = re.search(r'\d+', exp_str)
                        if exp_num:
                            experiencia_int = int(exp_num.group())
                    except:
                        pass
                
                # Mapear nivel de intención según urgencia
                nivel_intencion_map = {
                    'alta': 'decidido',
                    'media': 'explorando',
                    'baja': 'cotizando',
                    'muy alta': 'listo',
                    'inmediata': 'listo'
                }
                
                urgencia_lower = (prospecto['urgencia'] or '').lower()
                nivel_intencion = None
                for key, value in nivel_intencion_map.items():
                    if key in urgencia_lower:
                        nivel_intencion = value
                        break
                
                # Insertar en leads usando tu esquema exacto
                cursor.execute("""
                    INSERT INTO leads (
                        session_id, nombre, apellido, email, telefono,
                        carrera_interes, experiencia_laboral, plan,
                        nivel_intencion, estado, canal_origen
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        apellido = EXCLUDED.apellido,
                        email = EXCLUDED.email,
                        telefono = EXCLUDED.telefono,
                        carrera_interes = EXCLUDED.carrera_interes,
                        experiencia_laboral = EXCLUDED.experiencia_laboral,
                        plan = EXCLUDED.plan,
                        nivel_intencion = EXCLUDED.nivel_intencion,
                        canal_origen = EXCLUDED.canal_origen,
                        updated_at = NOW()
                """, (
                    session_id,                          # session_id (VARCHAR)
                    prospecto['nombre'],                 # nombre
                    prospecto['apellidos'],              # apellido
                    prospecto['email_1'],                # email
                    prospecto['telefono_1'],             # telefono (original)
                    prospecto['carrera_postula'],        # carrera_interes
                    experiencia_int,                     # experiencia_laboral (INTEGER)
                    prospecto['programa'],               # plan (Regular/Especial)
                    nivel_intencion,                     # nivel_intencion
                    'nuevo',                             # estado
                    prospecto['canal'] or 'importacion' # canal_origen
                ))
                
                # Actualizar estado en prospectos_raw
                cursor.execute("""
                    UPDATE prospectos_raw 
                    SET estado = 'activado', updated_at = NOW()
                    WHERE id = %s
                """, (prospecto['id'],))
                
                activated += 1
                print(f"✅ Prospecto ID {prospecto['id']} → Lead {session_id}")
                
            except Exception as e:
                skipped += 1
                error_msg = f"ID {prospecto['id']}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Mensaje de respuesta
        message_parts = []
        if activated > 0:
            message_parts.append(f'{activated} activados')
        if skipped > 0:
            message_parts.append(f'{skipped} omitidos')
        
        response = {
            'success': True,
            'activated': activated,
            'skipped': skipped,
            'message': ' | '.join(message_parts) if message_parts else 'Sin cambios'
        }
        
        if errors and len(errors) <= 5:
            response['warnings'] = errors
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error en activar_prospectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'activated': 0,
            'skipped': 0
        }), 500
    
@prospectos_bp.route('/api/stats')
def get_stats():
    """Obtiene estadísticas de prospectos"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'prospectos_raw'
            );
        """)
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'stats': {
                    'total': 0,
                    'por_propietario': [],
                    'ultimos_lotes': []
                }
            })
        
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM prospectos_raw
            WHERE NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
            )
        """)
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT propietario, COUNT(*) as count 
            FROM prospectos_raw 
            WHERE propietario IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
              )
            GROUP BY propietario 
            ORDER BY count DESC 
            LIMIT 5
        """)
        por_propietario = cursor.fetchall()
        
        cursor.execute("""
            SELECT lote_importacion, COUNT(*) as count, 
                   MIN(fecha_importacion) as fecha
            FROM prospectos_raw 
            WHERE lote_importacion IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.telefono = prospectos_raw.telefono_1
              )
            GROUP BY lote_importacion 
            ORDER BY fecha DESC 
            LIMIT 5
        """)
        ultimos_lotes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'por_propietario': por_propietario,
                'ultimos_lotes': ultimos_lotes
            }
        })
    
    except Exception as e:
        print(f"Error in get_stats: {str(e)}")
        return jsonify({
            'success': True,
            'stats': {
                'total': 0,
                'por_propietario': [],
                'ultimos_lotes': []
            }
        })