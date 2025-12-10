from flask import Blueprint, render_template, jsonify, request
from database_kb import get_kb_db_connection  # ← LÍNEA CORREGIDA
import os
import json
from datetime import datetime
import uuid

knowledge_base_bp = Blueprint('knowledge_base', __name__)

@knowledge_base_bp.route('/')
@knowledge_base_bp.route('/bases')
def knowledge_bases():
    """Vista principal - Lista de bases de conocimiento"""
    return render_template('modules/knowledge_bases.html', current_module='knowledge_base')

@knowledge_base_bp.route('/<kb_id>')
def knowledge_base_detail(kb_id):
    """Vista de detalle de una base de conocimiento específica"""
    return render_template('modules/knowledge_base_detail.html', 
                         current_module='knowledge_base',
                         kb_id=kb_id)

# ============================================
# API ENDPOINTS - KNOWLEDGE BASES
# ============================================

@knowledge_base_bp.route('/api/bases/list')
def list_bases():
    """Listar todas las bases de conocimiento con estadísticas"""
    try:
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Obtener bases con estadísticas
        cursor.execute("""
            SELECT 
                id, nombre, descripcion, qdrant_collection_name,
                vector_dimension, embedding_model, total_points,
                synced_points, last_synced_at, created_at, updated_at
            FROM knowledge_bases
            ORDER BY created_at DESC
        """)
        
        bases = cursor.fetchall()
        
        # Calcular estadísticas globales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bases,
                COALESCE(SUM(total_points), 0) as total_points,
                COALESCE(SUM(synced_points), 0) as synced_points,
                MAX(last_synced_at) as last_sync
            FROM knowledge_bases
        """)
        
        stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Formatear respuesta
        bases_list = []
        for base in bases:
            pending = base['total_points'] - base['synced_points']
            
            # Determinar estado de sincronización
            if base['total_points'] == 0:
                sync_status = 'empty'
                sync_label = 'Vacía'
                sync_color = 'secondary'
            elif base['synced_points'] == base['total_points']:
                sync_status = 'synced'
                sync_label = 'Sincronizado'
                sync_color = 'success'
            elif base['synced_points'] > 0:
                sync_status = 'partial'
                sync_label = f'{pending} pendientes'
                sync_color = 'warning'
            else:
                sync_status = 'pending'
                sync_label = 'Sin sincronizar'
                sync_color = 'danger'
            
            bases_list.append({
                'id': str(base['id']),
                'nombre': base['nombre'],
                'descripcion': base['descripcion'] or '',
                'collection_name': base['qdrant_collection_name'],
                'total_points': base['total_points'],
                'synced_points': base['synced_points'],
                'pending_points': pending,
                'last_synced_at': base['last_synced_at'].isoformat() if base['last_synced_at'] else None,
                'created_at': base['created_at'].isoformat() if base['created_at'] else None,
                'sync_status': sync_status,
                'sync_label': sync_label,
                'sync_color': sync_color
            })
        
        return jsonify({
            'success': True,
            'bases': bases_list,
            'stats': {
                'total_bases': stats['total_bases'],
                'total_points': stats['total_points'],
                'synced_points': stats['synced_points'],
                'pending_points': stats['total_points'] - stats['synced_points'],
                'last_sync': stats['last_sync'].isoformat() if stats['last_sync'] else None
            }
        })
        
    except Exception as e:
        print(f"Error en list_bases: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/bases/create', methods=['POST'])
def create_base():
    """Crear una nueva base de conocimiento"""
    try:
        data = request.get_json()
        
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()
        collection_name = data.get('collection_name', '').strip()
        
        if not nombre:
            return jsonify({'success': False, 'error': 'El nombre es obligatorio'}), 400
        
        if not collection_name:
            # Generar nombre de colección automáticamente
            collection_name = nombre.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            collection_name = ''.join(c for c in collection_name if c.isalnum() or c == '_')
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verificar que no exista una base con el mismo nombre de colección
        cursor.execute("""
            SELECT id FROM knowledge_bases 
            WHERE qdrant_collection_name = %s
        """, (collection_name,))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'error': f'Ya existe una base con el nombre de colección "{collection_name}"'
            }), 400
        
        # Crear la base de conocimiento
        cursor.execute("""
            INSERT INTO knowledge_bases (
                nombre, descripcion, qdrant_collection_name
            ) VALUES (%s, %s, %s)
            RETURNING id, nombre, qdrant_collection_name, created_at
        """, (nombre, descripcion, collection_name))
        
        new_base = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Base de conocimiento "{nombre}" creada exitosamente',
            'base': {
                'id': str(new_base['id']),
                'nombre': new_base['nombre'],
                'collection_name': new_base['qdrant_collection_name'],
                'created_at': new_base['created_at'].isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error en create_base: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/bases/<kb_id>', methods=['GET'])
def get_base(kb_id):
    """Obtener información de una base de conocimiento específica"""
    try:
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, nombre, descripcion, qdrant_collection_name,
                vector_dimension, embedding_model, total_points,
                synced_points, last_synced_at, created_at, updated_at
            FROM knowledge_bases
            WHERE id = %s
        """, (kb_id,))
        
        base = cursor.fetchone()
        
        if not base:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Base de conocimiento no encontrada'}), 404
        
        cursor.close()
        conn.close()
        
        pending = base['total_points'] - base['synced_points']
        
        return jsonify({
            'success': True,
            'base': {
                'id': str(base['id']),
                'nombre': base['nombre'],
                'descripcion': base['descripcion'] or '',
                'collection_name': base['qdrant_collection_name'],
                'vector_dimension': base['vector_dimension'],
                'embedding_model': base['embedding_model'],
                'total_points': base['total_points'],
                'synced_points': base['synced_points'],
                'pending_points': pending,
                'last_synced_at': base['last_synced_at'].isoformat() if base['last_synced_at'] else None,
                'created_at': base['created_at'].isoformat() if base['created_at'] else None
            }
        })
        
    except Exception as e:
        print(f"Error en get_base: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/bases/<kb_id>', methods=['DELETE'])
def delete_base(kb_id):
    """Eliminar una base de conocimiento y todos sus puntos"""
    try:
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Obtener info de la base antes de eliminar
        cursor.execute("""
            SELECT nombre, qdrant_collection_name 
            FROM knowledge_bases 
            WHERE id = %s
        """, (kb_id,))
        
        base = cursor.fetchone()
        
        if not base:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Base de conocimiento no encontrada'}), 404
        
        # Eliminar la base (cascade eliminará los puntos)
        cursor.execute("DELETE FROM knowledge_bases WHERE id = %s", (kb_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # TODO: También eliminar la colección de Qdrant
        
        return jsonify({
            'success': True,
            'message': f'Base de conocimiento "{base["nombre"]}" eliminada exitosamente'
        })
        
    except Exception as e:
        print(f"Error en delete_base: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# API ENDPOINTS - KNOWLEDGE POINTS
# ============================================

@knowledge_base_bp.route('/api/bases/<kb_id>/points')
def list_points(kb_id):
    """Listar puntos de una base de conocimiento"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        search = request.args.get('search', '').strip()
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Construir query con búsqueda
        where_clause = "knowledge_base_id = %s"
        params = [kb_id]
        
        if search:
            where_clause += " AND (page_content ILIKE %s OR metadata::text ILIKE %s)"
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) as total FROM knowledge_points WHERE {where_clause}", params)
        total = cursor.fetchone()['total']
        
        # Obtener puntos paginados
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        cursor.execute(f"""
            SELECT 
                id, page_content, metadata, synced_to_qdrant,
                qdrant_point_id, created_at, updated_at
            FROM knowledge_points
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])
        
        points = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formatear respuesta
        points_list = []
        for point in points:
            # Truncar page_content para lista
            content_preview = point['page_content'][:150] + '...' if len(point['page_content']) > 150 else point['page_content']
            
            points_list.append({
                'id': str(point['id']),
                'page_content': point['page_content'],
                'content_preview': content_preview,
                'metadata': point['metadata'] or {},
                'synced': point['synced_to_qdrant'],
                'qdrant_id': str(point['qdrant_point_id']) if point['qdrant_point_id'] else None,
                'created_at': point['created_at'].isoformat() if point['created_at'] else None,
                'updated_at': point['updated_at'].isoformat() if point['updated_at'] else None
            })
        
        return jsonify({
            'success': True,
            'points': points_list,
            'total': total,
            'page': page,
            'total_pages': total_pages,
            'page_size': page_size
        })
        
    except Exception as e:
        print(f"Error en list_points: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/bases/<kb_id>/points/create', methods=['POST'])
def create_point(kb_id):
    """Crear un nuevo punto en la base de conocimiento"""
    try:
        data = request.get_json()
        
        page_content = data.get('page_content', '').strip()
        metadata = data.get('metadata', {})
        
        if not page_content:
            return jsonify({'success': False, 'error': 'El contenido (pageContent) es obligatorio'}), 400
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verificar que la base existe
        cursor.execute("SELECT id FROM knowledge_bases WHERE id = %s", (kb_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Base de conocimiento no encontrada'}), 404
        
        # Crear el punto (sin sincronizar aún)
        cursor.execute("""
            INSERT INTO knowledge_points (
                knowledge_base_id, page_content, metadata, synced_to_qdrant
            ) VALUES (%s, %s, %s, false)
            RETURNING id, page_content, metadata, created_at
        """, (kb_id, page_content, json.dumps(metadata) if metadata else None))
        
        new_point = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Punto creado exitosamente. Sincroniza para subirlo a Qdrant.',
            'point': {
                'id': str(new_point['id']),
                'page_content': new_point['page_content'],
                'metadata': new_point['metadata'] or {},
                'synced': False,
                'created_at': new_point['created_at'].isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error en create_point: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@knowledge_base_bp.route('/api/bases/<kb_id>/points/import', methods=['POST'])
def import_points_batch(kb_id):
    """Importar múltiples puntos desde JSON"""
    try:
        data = request.get_json()
        points = data.get('points', [])
        
        if not points or not isinstance(points, list):
            return jsonify({
                'success': False,
                'error': 'Se requiere un array de puntos'
            }), 400
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Error de conexión a la base de datos'
            }), 500
        
        cursor = conn.cursor()
        
        # Verificar que la base existe
        cursor.execute("SELECT id FROM knowledge_bases WHERE id = %s", (kb_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Base de conocimiento no encontrada'
            }), 404
        
        # Insertar puntos en batch
        inserted = 0
        errors = []
        
        for idx, point in enumerate(points):
            try:
                page_content = point.get('pageContent', '').strip()
                metadata = point.get('metadata', {})
                
                if not page_content:
                    errors.append(f"Punto {idx + 1}: pageContent vacío")
                    continue
                
                point_id = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT INTO knowledge_points 
                    (id, knowledge_base_id, page_content, metadata, synced_to_qdrant)
                    VALUES (%s, %s, %s, %s, false)
                """, (point_id, kb_id, page_content, json.dumps(metadata)))
                
                inserted += 1
                
            except Exception as e:
                errors.append(f"Punto {idx + 1}: {str(e)}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{inserted} puntos importados exitosamente',
            'imported': inserted,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        print(f"Error importing points: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@knowledge_base_bp.route('/api/points/<point_id>', methods=['GET'])
def get_point(point_id):
    """Obtener un punto específico"""
    try:
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, knowledge_base_id, page_content, metadata,
                synced_to_qdrant, qdrant_point_id, created_at, updated_at
            FROM knowledge_points
            WHERE id = %s
        """, (point_id,))
        
        point = cursor.fetchone()
        
        if not point:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Punto no encontrado'}), 404
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'point': {
                'id': str(point['id']),
                'kb_id': str(point['knowledge_base_id']),
                'page_content': point['page_content'],
                'metadata': point['metadata'] or {},
                'synced': point['synced_to_qdrant'],
                'qdrant_id': str(point['qdrant_point_id']) if point['qdrant_point_id'] else None,
                'created_at': point['created_at'].isoformat() if point['created_at'] else None,
                'updated_at': point['updated_at'].isoformat() if point['updated_at'] else None
            }
        })
        
    except Exception as e:
        print(f"Error en get_point: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/points/<point_id>', methods=['PUT'])
def update_point(point_id):
    """Actualizar un punto existente"""
    try:
        data = request.get_json()
        
        page_content = data.get('page_content', '').strip()
        metadata = data.get('metadata', {})
        
        if not page_content:
            return jsonify({'success': False, 'error': 'El contenido no puede estar vacío'}), 400
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Actualizar punto y marcar como no sincronizado
        cursor.execute("""
            UPDATE knowledge_points
            SET page_content = %s,
                metadata = %s,
                synced_to_qdrant = false,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, page_content, metadata, updated_at
        """, (page_content, json.dumps(metadata) if metadata else None, point_id))
        
        updated_point = cursor.fetchone()
        
        if not updated_point:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Punto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Punto actualizado. Sincroniza para actualizar en Qdrant.',
            'point': {
                'id': str(updated_point['id']),
                'page_content': updated_point['page_content'],
                'metadata': updated_point['metadata'] or {},
                'synced': False,
                'updated_at': updated_point['updated_at'].isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error en update_point: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@knowledge_base_bp.route('/api/points/<point_id>', methods=['DELETE'])
def delete_point(point_id):
    """Eliminar un punto"""
    try:
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Obtener info antes de eliminar
        cursor.execute("""
            SELECT qdrant_point_id, synced_to_qdrant
            FROM knowledge_points
            WHERE id = %s
        """, (point_id,))
        
        point = cursor.fetchone()
        
        if not point:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Punto no encontrado'}), 404
        
        # Eliminar de PostgreSQL
        cursor.execute("DELETE FROM knowledge_points WHERE id = %s", (point_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # TODO: También eliminar de Qdrant si estaba sincronizado
        
        return jsonify({
            'success': True,
            'message': 'Punto eliminado exitosamente'
        })
        
    except Exception as e:
        print(f"Error en delete_point: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@knowledge_base_bp.route('/api/bases/<kb_id>/sync', methods=['POST'])
def sync_base_to_qdrant(kb_id):
    """Sincronizar todos los puntos pendientes de una base con Qdrant"""
    try:
        from .qdrant_manager import QdrantManager
        from .embedding_manager import EmbeddingManager
        
        conn = get_kb_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Error de conexión a la base de datos'
            }), 500
        
        cursor = conn.cursor()
        
        # Obtener información de la base
        cursor.execute("""
            SELECT id, nombre, qdrant_collection_name, vector_dimension, embedding_model
            FROM knowledge_bases 
            WHERE id = %s
        """, (kb_id,))
        
        base = cursor.fetchone()
        if not base:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Base de conocimiento no encontrada'
            }), 404
        
        # Obtener puntos pendientes de sincronización
        cursor.execute("""
            SELECT id, page_content, metadata
            FROM knowledge_points
            WHERE knowledge_base_id = %s 
            AND synced_to_qdrant = false
            ORDER BY created_at ASC
        """, (kb_id,))
        
        pending_points = cursor.fetchall()
        
        if not pending_points or len(pending_points) == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'message': 'No hay puntos pendientes de sincronización',
                'synced': 0
            })
        
        # Inicializar managers
        qdrant = QdrantManager()
        embeddings_mgr = EmbeddingManager()
        
        # Verificar/crear colección en Qdrant
        collection_name = base['qdrant_collection_name']
        if not qdrant.collection_exists(collection_name):
            result = qdrant.create_collection(collection_name, base['vector_dimension'])
            if not result['success']:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'error': f'Error creando colección en Qdrant: {result["error"]}'
                }), 500
        
        # Procesar en batches de 50 puntos
        batch_size = 50
        total_synced = 0
        total_errors = 0
        errors_detail = []
        
        for i in range(0, len(pending_points), batch_size):
            batch = pending_points[i:i + batch_size]
            
            # Extraer textos para generar embeddings
            texts = [point['page_content'] for point in batch]
            
            # Generar embeddings en batch
            embeddings_result = embeddings_mgr.generate_embeddings_batch(texts)
            
            if not embeddings_result['success']:
                error_msg = f"Error generando embeddings para batch {i//batch_size + 1}: {embeddings_result['error']}"
                errors_detail.append(error_msg)
                total_errors += len(batch)
                continue
            
            # Preparar puntos para Qdrant
            qdrant_points = []
            for idx, point in enumerate(batch):
                qdrant_points.append({
                    'id': point['id'],
                    'vector': embeddings_result['embeddings'][idx],
                    'payload': {
                        'page_content': point['page_content'],
                        'metadata': point['metadata']
                    }
                })
            
            # Upsert en Qdrant
            upsert_result = qdrant.upsert_points_batch(collection_name, qdrant_points)
            
            if upsert_result['success']:
                # Actualizar estado en PostgreSQL
                point_ids = [point['id'] for point in batch]
                cursor.execute("""
                    UPDATE knowledge_points
                    SET synced_to_qdrant = true,
                        qdrant_point_id = id
                    WHERE id = ANY(%s::uuid[])
                """, (point_ids,))
                
                total_synced += len(batch)
            else:
                error_msg = f"Error sincronizando batch {i//batch_size + 1} con Qdrant: {upsert_result['error']}"
                errors_detail.append(error_msg)
                total_errors += len(batch)
        
        # Actualizar last_synced_at en la base
        cursor.execute("""
            UPDATE knowledge_bases
            SET last_synced_at = NOW()
            WHERE id = %s
        """, (kb_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Calcular costo estimado
        total_tokens = embeddings_result.get('total_tokens', 0) if 'embeddings_result' in locals() else 0
        cost_info = embeddings_mgr.estimate_cost(total_tokens) if total_tokens > 0 else None
        
        return jsonify({
            'success': True,
            'message': f'{total_synced} puntos sincronizados exitosamente',
            'synced': total_synced,
            'errors': total_errors,
            'errors_detail': errors_detail if errors_detail else None,
            'total_points': len(pending_points),
            'cost': cost_info
        })
        
    except Exception as e:
        print(f"Error syncing base: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500