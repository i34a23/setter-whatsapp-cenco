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
    """API para listar prospectos activos con paginación"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        search = request.args.get('search', '').strip()
        
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
        
        # Construir query con o sin LEFT JOIN según exista la tabla
        if chat_exists:
            query = f"""
                SELECT 
                    l.id, l.nombre, l.apellido, l.email, l.telefono, l.carrera_interes,
                    l.experiencia_laboral, l.plan, l.estado, l.nivel_intencion,
                    l.dias_transcurridos, l.descuento_actual,
                    l.followup_dia3_enviado, l.followup_dia3_fecha,
                    l.followup_dia5_enviado, l.followup_dia5_fecha,
                    l.followup_dia6_enviado, l.followup_dia6_fecha,
                    l.followup_dia8_enviado, l.followup_dia8_fecha,
                    l.derivado_a_humano, l.agente_asignado,
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
                ORDER BY l.dias_transcurridos DESC, l.updated_at DESC
                LIMIT %s OFFSET %s
            """
        else:
            query = f"""
                SELECT 
                    id, nombre, apellido, email, telefono, carrera_interes,
                    experiencia_laboral, plan, estado, nivel_intencion,
                    dias_transcurridos, descuento_actual,
                    followup_dia3_enviado, followup_dia3_fecha,
                    followup_dia5_enviado, followup_dia5_fecha,
                    followup_dia6_enviado, followup_dia6_fecha,
                    followup_dia8_enviado, followup_dia8_fecha,
                    derivado_a_humano, agente_asignado,
                    created_at, updated_at,
                    0 as mensaje_count
                FROM leads
                WHERE {where_sql}
                ORDER BY dias_transcurridos DESC, updated_at DESC
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
        
        # Obtener datos del prospecto
        cursor.execute("""
            SELECT nombre, apellido, email, telefono, carrera_interes, plan, estado
            FROM leads
            WHERE telefono = %s
            LIMIT 1
        """, [telefono])
        
        prospecto_data = cursor.fetchone()
        
        # Obtener mensajes usando session_id = telefono
        # Nota: n8n_chat_histories solo tiene id, session_id, message
        # Intentar con y sin prefijo 56
        cursor.execute("""
            SELECT id, session_id, message
            FROM n8n_chat_histories
            WHERE session_id = %s 
               OR session_id = CONCAT('56', %s)
               OR REPLACE(session_id, '56', '') = %s
            ORDER BY id ASC
        """, [telefono, telefono, telefono])
        
        mensajes_raw = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Parsear mensajes JSONB
        mensajes = []
        for msg in mensajes_raw:
            try:
                # El campo message es JSONB, ya viene como dict
                mensaje_data = msg['message'] if isinstance(msg['message'], dict) else {}
                
                # Extraer tipo y contenido del mensaje
                # Formato n8n: {"type": "human"/"ai", "content": "texto"}
                msg_type = mensaje_data.get('type', 'text')
                content = mensaje_data.get('content', '')
                
                # Si no hay content, intentar con data o text
                if not content:
                    content = mensaje_data.get('data', mensaje_data.get('text', str(mensaje_data)))
                
                mensajes.append({
                    'id': msg['id'],
                    'type': msg_type,
                    'content': content,
                    'timestamp': None,  # n8n_chat_histories no tiene timestamp
                    'is_ai': msg_type == 'ai',
                    'is_human': msg_type == 'human'
                })
            except Exception as e:
                print(f"Error parsing message {msg.get('id')}: {str(e)}")
                continue
        
        # Formatear datos del prospecto
        prospecto = None
        if prospecto_data:
            prospecto = {
                'nombre': prospecto_data['nombre'] or '',
                'apellido': prospecto_data['apellido'] or '',
                'email': prospecto_data['email'] or '',
                'telefono': prospecto_data['telefono'] or '',
                'carrera': prospecto_data['carrera_interes'] or '',
                'plan': prospecto_data['plan'] or '',
                'estado': prospecto_data['estado'] or ''
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
    """Obtiene estadísticas de prospectos activos"""
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
                    'por_estado': [],
                    'por_plan': []
                }
            })
        
        # Total activos
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM leads
        """)
        total_activos = cursor.fetchone()['total']
        
        # Por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as count
            FROM leads
            WHERE estado IS NOT NULL
            GROUP BY estado
            ORDER BY count DESC
        """)
        por_estado = cursor.fetchall()
        
        # Por plan
        cursor.execute("""
            SELECT plan, COUNT(*) as count
            FROM leads
            WHERE plan IS NOT NULL
            GROUP BY plan
            ORDER BY count DESC
        """)
        por_plan = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_activos': total_activos,
                'por_estado': por_estado,
                'por_plan': por_plan
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
                'por_estado': [],
                'por_plan': []
            }
        })