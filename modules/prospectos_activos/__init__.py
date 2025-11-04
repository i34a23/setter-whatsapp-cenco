from flask import Blueprint, render_template, jsonify, request
from database import get_db_connection
from datetime import datetime

prospectos_activos_bp = Blueprint('prospectos_activos', __name__)

@prospectos_activos_bp.route('/')
@prospectos_activos_bp.route('/activos')
def prospectos_activos():
    """Vista principal de prospectos activos"""
    return render_template('modules/prospectos_activos.html', current_module='prospectos_activos')

@prospectos_activos_bp.route('/api/list')
def list_activos():
    """API para listar prospectos activos con paginación y filtros"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        search = request.args.get('search', '').strip()
        
        # Nuevos parámetros de filtro
        filter_estado = request.args.get('estado', '').strip()
        filter_carrera = request.args.get('carrera', '').strip()
        filter_plan = request.args.get('plan', '').strip()
        
        # Parámetros de ordenamiento
        sort_by = request.args.get('sort_by', 'dias_transcurridos')
        sort_order = request.args.get('sort_order', 'DESC')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'leads'
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
                'page': page,
                'total_pages': 0
            })
        
        # Construir WHERE clause
        where_clauses = []
        params = []
        
        if search:
            search_pattern = f'%{search}%'
            where_clauses.append("""
                (nombre ILIKE %s OR apellido ILIKE %s OR 
                 email ILIKE %s OR carrera_interes ILIKE %s)
            """)
            params.extend([search_pattern] * 4)
        
        # Filtros adicionales
        if filter_estado:
            where_clauses.append("estado = %s")
            params.append(filter_estado)
        
        if filter_carrera:
            where_clauses.append("carrera_interes = %s")
            params.append(filter_carrera)
        
        if filter_plan:
            where_clauses.append("plan = %s")
            params.append(filter_plan)
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) as total FROM leads WHERE {where_sql}", params)
        total = cursor.fetchone()['total']
        
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Verificar si existe la tabla n8n_chat_histories
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'n8n_chat_histories'
            );
        """)
        chat_exists = cursor.fetchone()['exists']
        
        # Validar columna de ordenamiento
        valid_sort_columns = {
            'nombre': 'l.nombre',
            'apellido': 'l.apellido',
            'carrera': 'l.carrera_interes',
            'dias_transcurridos': 'l.dias_transcurridos',
            'mensaje_count': 'mensaje_count',
            'fecha_primer_contacto': 'l.fecha_primer_contacto'
        }
        
        sort_column = valid_sort_columns.get(sort_by, 'l.dias_transcurridos')
        sort_direction = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
        
        # Construir query con o sin LEFT JOIN según exista la tabla
        if chat_exists:
            query = f"""
                SELECT 
                    l.id, l.nombre, l.apellido, l.email, l.telefono, l.carrera_interes,
                    l.experiencia_laboral, l.plan, l.estado, l.nivel_intencion,
                    l.dias_transcurridos, l.descuento_actual, l.fecha_primer_contacto,
                    l.followup_dia3_enviado, l.followup_dia3_fecha,
                    l.followup_dia5_enviado, l.followup_dia5_fecha,
                    l.followup_dia6_enviado, l.followup_dia6_fecha,
                    l.followup_dia8_enviado, l.followup_dia8_fecha,
                    l.derivado_a_humano, l.agente_asignado, l.chat_status, l.notas,
                    l.fecha_derivacion, l.razon_derivacion,
                    l.created_at, l.updated_at,
                    COALESCE(m.mensaje_count, 0) as mensaje_count
                FROM leads l
                LEFT JOIN (
                    SELECT session_id, COUNT(*) as mensaje_count
                    FROM n8n_chat_histories
                    GROUP BY session_id
                ) m ON (
                    l.telefono = m.session_id OR 
                    CONCAT('56', l.telefono) = m.session_id OR
                    l.telefono = REPLACE(m.session_id, '56', '')
                )
                WHERE {where_sql}
                ORDER BY {sort_column} {sort_direction}, l.updated_at DESC
                LIMIT %s OFFSET %s
            """
        else:
            query = f"""
                SELECT 
                    id, nombre, apellido, email, telefono, carrera_interes,
                    experiencia_laboral, plan, estado, nivel_intencion,
                    dias_transcurridos, descuento_actual, fecha_primer_contacto,
                    followup_dia3_enviado, followup_dia3_fecha,
                    followup_dia5_enviado, followup_dia5_fecha,
                    followup_dia6_enviado, followup_dia6_fecha,
                    followup_dia8_enviado, followup_dia8_fecha,
                    derivado_a_humano, agente_asignado, chat_status, notas,
                    fecha_derivacion, razon_derivacion,
                    created_at, updated_at,
                    0 as mensaje_count
                FROM leads
                WHERE {where_sql}
                ORDER BY {sort_column} {sort_direction}, updated_at DESC
                LIMIT %s OFFSET %s
            """
        
        cursor.execute(query, params + [page_size, offset])
        
        prospectos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formatear datos para respuesta
        data = []
        for p in prospectos:
            data.append({
                'id': str(p['id']),
                'nombre': p['nombre'] or '',
                'apellido': p['apellido'] or '',
                'email': p['email'] or '',
                'telefono': p['telefono'] or '',
                'carrera': p['carrera_interes'] or '',
                'experiencia': p['experiencia_laboral'] or 0,
                'plan': p['plan'] or '',
                'estado': p['estado'] or '',
                'nivel_intencion': p['nivel_intencion'] or '',
                'dias_transcurridos': p['dias_transcurridos'] or 0,
                'descuento_actual': p['descuento_actual'] or 0,
                'fecha_primer_contacto': p['fecha_primer_contacto'].strftime('%d/%m/%Y') if p['fecha_primer_contacto'] else '',
                'mensaje_count': p['mensaje_count'] or 0,
                'followups': {
                    'dia3': {
                        'enviado': p['followup_dia3_enviado'] or False,
                        'fecha': p['followup_dia3_fecha'].isoformat() if p['followup_dia3_fecha'] else None
                    },
                    'dia5': {
                        'enviado': p['followup_dia5_enviado'] or False,
                        'fecha': p['followup_dia5_fecha'].isoformat() if p['followup_dia5_fecha'] else None
                    },
                    'dia6': {
                        'enviado': p['followup_dia6_enviado'] or False,
                        'fecha': p['followup_dia6_fecha'].isoformat() if p['followup_dia6_fecha'] else None
                    },
                    'dia8': {
                        'enviado': p['followup_dia8_enviado'] or False,
                        'fecha': p['followup_dia8_fecha'].isoformat() if p['followup_dia8_fecha'] else None
                    }
                },
                'derivado_a_humano': p['derivado_a_humano'] or False,
                'agente_asignado': p['agente_asignado'],
                'chat_status': p['chat_status'] or '',
                'notas': p['notas'] or '',
                'fecha_derivacion': p['fecha_derivacion'].isoformat() if p['fecha_derivacion'] else None,
                'razon_derivacion': p['razon_derivacion'] or '',
                'created_at': p['created_at'].isoformat() if p['created_at'] else None,
                'updated_at': p['updated_at'].isoformat() if p['updated_at'] else None
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'total': total,
            'page': page,
            'total_pages': total_pages
        })
        
    except Exception as e:
        print(f"Error in list_activos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'data': [],
            'total': 0,
            'page': 1,
            'total_pages': 0
        })

@prospectos_activos_bp.route('/api/mensajes/<telefono>')
def get_mensajes(telefono):
    """API para obtener historial de mensajes de un prospecto"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla n8n_chat_histories
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'n8n_chat_histories'
            );
        """)
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'mensajes': [],
                'prospecto': None
            })
        
        # Obtener datos completos del prospecto
        cursor.execute("""
            SELECT 
                nombre, apellido, email, telefono, carrera_interes, plan, estado,
                nivel_intencion, descuento_actual, fecha_primer_contacto,
                followup_dia3_enviado, followup_dia3_fecha,
                followup_dia5_enviado, followup_dia5_fecha,
                followup_dia6_enviado, followup_dia6_fecha,
                followup_dia8_enviado, followup_dia8_fecha,
                derivado_a_humano, agente_asignado, fecha_derivacion,
                razon_derivacion, chat_status, notas
            FROM leads
            WHERE telefono = %s
            LIMIT 1
        """, [telefono])
        
        prospecto_data = cursor.fetchone()
        
        # Obtener mensajes usando session_id = telefono
        cursor.execute("""
            SELECT id, session_id, message, timestamp
            FROM n8n_chat_histories
            WHERE session_id = %s 
               OR session_id = CONCAT('56', %s)
               OR session_id = REPLACE(%s, '56', '')
            ORDER BY timestamp ASC
        """, [telefono, telefono, telefono])
        
        mensajes_raw = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Procesar mensajes
        mensajes = []
        for msg in mensajes_raw:
            try:
                import json
                message_data = json.loads(msg['message']) if isinstance(msg['message'], str) else msg['message']
                
                # Extraer rol y contenido
                if isinstance(message_data, dict):
                    role = message_data.get('type', 'user')
                    content = message_data.get('content', '')
                    
                    # Mapear tipos de n8n a roles estándar
                    if role == 'human':
                        role = 'user'
                    elif role == 'ai':
                        role = 'assistant'
                    
                    mensajes.append({
                        'id': msg['id'],
                        'role': role,
                        'content': content,
                        'timestamp': msg['timestamp'].isoformat() if msg['timestamp'] else None
                    })
            except Exception as e:
                print(f"Error procesando mensaje: {str(e)}")
                continue
        
        # Formatear datos del prospecto con información completa
        prospecto = None
        if prospecto_data:
            prospecto = {
                'nombre': prospecto_data['nombre'] or '',
                'apellido': prospecto_data['apellido'] or '',
                'email': prospecto_data['email'] or '',
                'telefono': prospecto_data['telefono'] or '',
                'carrera': prospecto_data['carrera_interes'] or '',
                'plan': prospecto_data['plan'] or '',
                'estado': prospecto_data['estado'] or '',
                'nivel_intencion': prospecto_data['nivel_intencion'] or '',
                'descuento_actual': prospecto_data['descuento_actual'] or 0,
                'fecha_primer_contacto': prospecto_data['fecha_primer_contacto'].strftime('%d/%m/%Y') if prospecto_data['fecha_primer_contacto'] else '',
                'followups': {
                    'dia3': {
                        'enviado': prospecto_data['followup_dia3_enviado'] or False,
                        'fecha': prospecto_data['followup_dia3_fecha'].strftime('%d/%m/%Y %H:%M') if prospecto_data['followup_dia3_fecha'] else None
                    },
                    'dia5': {
                        'enviado': prospecto_data['followup_dia5_enviado'] or False,
                        'fecha': prospecto_data['followup_dia5_fecha'].strftime('%d/%m/%Y %H:%M') if prospecto_data['followup_dia5_fecha'] else None
                    },
                    'dia6': {
                        'enviado': prospecto_data['followup_dia6_enviado'] or False,
                        'fecha': prospecto_data['followup_dia6_fecha'].strftime('%d/%m/%Y %H:%M') if prospecto_data['followup_dia6_fecha'] else None
                    },
                    'dia8': {
                        'enviado': prospecto_data['followup_dia8_enviado'] or False,
                        'fecha': prospecto_data['followup_dia8_fecha'].strftime('%d/%m/%Y %H:%M') if prospecto_data['followup_dia8_fecha'] else None
                    }
                },
                'derivado_a_humano': prospecto_data['derivado_a_humano'] or False,
                'agente_asignado': prospecto_data['agente_asignado'] or '',
                'fecha_derivacion': prospecto_data['fecha_derivacion'].strftime('%d/%m/%Y %H:%M') if prospecto_data['fecha_derivacion'] else '',
                'razon_derivacion': prospecto_data['razon_derivacion'] or '',
                'chat_status': prospecto_data['chat_status'] or '',
                'notas': prospecto_data['notas'] or ''
            }
        
        return jsonify({
            'success': True,
            'mensajes': mensajes,
            'prospecto': prospecto
        })
        
    except Exception as e:
        print(f"Error in get_mensajes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'mensajes': [],
            'prospecto': None
        })

@prospectos_activos_bp.route('/api/activar', methods=['POST'])
def activar_prospectos():
    """Activar múltiples prospectos (cambiar estado a 'en_proceso')"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({
                'success': False, 
                'error': 'No se proporcionaron IDs'
            }), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False, 
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        # Actualizar estado
        placeholders = ','.join(['%s'] * len(ids))
        query = f"""
            UPDATE leads 
            SET estado = 'en_proceso', updated_at = NOW()
            WHERE id IN ({placeholders})
            RETURNING id
        """
        cursor.execute(query, ids)
        
        updated = cursor.fetchall()
        updated_ids = [str(row['id']) for row in updated]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(updated_ids)} prospectos activados correctamente',
            'updated_ids': updated_ids
        })
        
    except Exception as e:
        print(f"Error en activar_prospectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prospectos_activos_bp.route('/api/cambiar-estado', methods=['POST'])
def cambiar_estado():
    """Cambiar estado de múltiples prospectos"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        nuevo_estado = data.get('estado', '')
        
        if not ids or not nuevo_estado:
            return jsonify({
                'success': False,
                'error': 'IDs y estado son requeridos'
            }), 400
        
        # Validar estado
        estados_validos = [
            'nuevo', 'calificando', 'persuadiendo', 
            'listo_matricula', 'perdido', 'en_proceso'
        ]
        
        if nuevo_estado not in estados_validos:
            return jsonify({
                'success': False,
                'error': f'Estado inválido. Permitidos: {", ".join(estados_validos)}'
            }), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        # Actualizar estado
        placeholders = ','.join(['%s'] * len(ids))
        query = f"""
            UPDATE leads 
            SET estado = %s, updated_at = NOW()
            WHERE id IN ({placeholders})
            RETURNING id
        """
        cursor.execute(query, [nuevo_estado] + ids)
        
        updated = cursor.fetchall()
        updated_ids = [str(row['id']) for row in updated]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(updated_ids)} prospectos actualizados a: {nuevo_estado}',
            'updated_ids': updated_ids
        })
        
    except Exception as e:
        print(f"Error en cambiar_estado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prospectos_activos_bp.route('/api/stats')
def get_stats():
    """Obtiene estadísticas de prospectos activos por estado"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'leads'
            );
        """)
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'stats': {
                    'total_activos': 0,
                    'por_estado': []
                }
            })
        
        # Total activos
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM leads
        """)
        total_activos = cursor.fetchone()['total']
        
        # Por estado con nombres descriptivos
        cursor.execute("""
            SELECT 
                estado, 
                COUNT(*) as count
            FROM leads
            WHERE estado IS NOT NULL
            GROUP BY estado
            ORDER BY count DESC
        """)
        por_estado_raw = cursor.fetchall()
        
        # Mapeo de estados a nombres descriptivos
        estado_nombres = {
            'nuevo': 'Nuevo',
            'calificando': 'Calificando',
            'persuadiendo': 'Persuadiendo',
            'listo_matricula': 'Listo para Matrícula',
            'perdido': 'Perdido',
            'en_proceso': 'En Proceso'
        }
        
        # Mapeo de estados a colores
        estado_colores = {
            'nuevo': 'primary',
            'calificando': 'info',
            'persuadiendo': 'warning',
            'listo_matricula': 'success',
            'perdido': 'danger',
            'en_proceso': 'secondary'
        }
        
        por_estado = []
        for row in por_estado_raw:
            estado_key = row['estado']
            por_estado.append({
                'estado': estado_key,
                'nombre': estado_nombres.get(estado_key, estado_key),
                'color': estado_colores.get(estado_key, 'secondary'),
                'count': row['count']
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_activos': total_activos,
                'por_estado': por_estado
            }
        })
        
    except Exception as e:
        print(f"Error in get_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'stats': {
                'total_activos': 0,
                'por_estado': []
            }
        })

@prospectos_activos_bp.route('/api/filter-options')
def get_filter_options():
    """Obtiene las opciones disponibles para los filtros tipo Excel"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'leads'
            );
        """)
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'options': {
                    'carreras': [],
                    'planes': [],
                    'estados': []
                }
            })
        
        # Obtener carreras únicas
        cursor.execute("""
            SELECT DISTINCT carrera_interes
            FROM leads
            WHERE carrera_interes IS NOT NULL AND carrera_interes != ''
            ORDER BY carrera_interes
        """)
        carreras = [row['carrera_interes'] for row in cursor.fetchall()]
        
        # Obtener planes únicos
        cursor.execute("""
            SELECT DISTINCT plan
            FROM leads
            WHERE plan IS NOT NULL AND plan != ''
            ORDER BY plan
        """)
        planes = [row['plan'] for row in cursor.fetchall()]
        
        # Obtener estados únicos
        cursor.execute("""
            SELECT DISTINCT estado
            FROM leads
            WHERE estado IS NOT NULL AND estado != ''
            ORDER BY estado
        """)
        estados = [row['estado'] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'options': {
                'carreras': carreras,
                'planes': planes,
                'estados': estados
            }
        })
        
    except Exception as e:
        print(f"Error in get_filter_options: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'options': {
                'carreras': [],
                'planes': [],
                'estados': []
            }
        })