import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import uuid

class QdrantManager:
    """Gestor de conexión y operaciones con Qdrant"""
    
    def __init__(self):
        self.url = os.getenv('QDRANT_URL')
        self.api_key = os.getenv('QDRANT_API_KEY')
        
        if not self.url or not self.api_key:
            raise ValueError("QDRANT_URL y QDRANT_API_KEY deben estar configurados en .env")
        
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=30
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con Qdrant"""
        try:
            collections = self.client.get_collections()
            return {
                'success': True,
                'message': 'Conexión exitosa con Qdrant',
                'collections_count': len(collections.collections)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def collection_exists(self, collection_name: str) -> bool:
        """Verificar si una colección existe"""
        try:
            collections = self.client.get_collections()
            return any(col.name == collection_name for col in collections.collections)
        except Exception as e:
            print(f"Error verificando colección: {str(e)}")
            return False
    
    def create_collection(self, collection_name: str, vector_size: int = 3072) -> Dict[str, Any]:
        """Crear una nueva colección en Qdrant"""
        try:
            # Verificar si ya existe
            if self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" ya existe'
                }
            
            # Crear colección
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            
            return {
                'success': True,
                'message': f'Colección "{collection_name}" creada exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Eliminar una colección de Qdrant"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            self.client.delete_collection(collection_name=collection_name)
            
            return {
                'success': True,
                'message': f'Colección "{collection_name}" eliminada exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Obtener información de una colección"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            info = self.client.get_collection(collection_name=collection_name)
            
            return {
                'success': True,
                'info': {
                    'name': collection_name,
                    'points_count': info.points_count,
                    'vectors_count': info.vectors_count,
                    'status': info.status,
                    'optimizer_status': info.optimizer_status
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upsert_point(
        self, 
        collection_name: str, 
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insertar o actualizar un punto en Qdrant"""
        try:
            # Verificar que la colección existe
            if not self.collection_exists(collection_name):
                # Crear colección si no existe
                result = self.create_collection(collection_name, len(vector))
                if not result['success']:
                    return result
            
            # Crear punto
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            # Upsert (insert or update)
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            return {
                'success': True,
                'message': f'Punto {point_id} sincronizado exitosamente'
            }
            
        except Exception as e:
            print(f"Error en upsert_point: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def upsert_points_batch(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Insertar o actualizar múltiples puntos en batch"""
        try:
            # Verificar que la colección existe
            if not self.collection_exists(collection_name):
                # Crear colección con el tamaño del primer vector
                if points and 'vector' in points[0]:
                    vector_size = len(points[0]['vector'])
                    result = self.create_collection(collection_name, vector_size)
                    if not result['success']:
                        return result
            
            # Preparar puntos
            point_structs = []
            for point_data in points:
                point = PointStruct(
                    id=point_data['id'],
                    vector=point_data['vector'],
                    payload=point_data['payload']
                )
                point_structs.append(point)
            
            # Upsert en batch
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            return {
                'success': True,
                'message': f'{len(points)} puntos sincronizados exitosamente',
                'synced_count': len(points)
            }
            
        except Exception as e:
            print(f"Error en upsert_points_batch: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_point(self, collection_name: str, point_id: str) -> Dict[str, Any]:
        """Eliminar un punto de Qdrant"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            
            return {
                'success': True,
                'message': f'Punto {point_id} eliminado exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_points_batch(
        self,
        collection_name: str,
        point_ids: List[str]
    ) -> Dict[str, Any]:
        """Eliminar múltiples puntos en batch"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
            
            return {
                'success': True,
                'message': f'{len(point_ids)} puntos eliminados exitosamente',
                'deleted_count': len(point_ids)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Buscar puntos similares por vector"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            # Realizar búsqueda
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Formatear resultados
            points = []
            for result in results:
                points.append({
                    'id': str(result.id),
                    'score': result.score,
                    'payload': result.payload
                })
            
            return {
                'success': True,
                'results': points,
                'count': len(points)
            }
            
        except Exception as e:
            print(f"Error en search_similar: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_point(self, collection_name: str, point_id: str) -> Dict[str, Any]:
        """Obtener un punto específico de Qdrant"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return {
                    'success': False,
                    'error': f'Punto {point_id} no encontrado'
                }
            
            point = points[0]
            
            return {
                'success': True,
                'point': {
                    'id': str(point.id),
                    'payload': point.payload
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def count_points(self, collection_name: str) -> Dict[str, Any]:
        """Contar puntos en una colección"""
        try:
            if not self.collection_exists(collection_name):
                return {
                    'success': False,
                    'error': f'La colección "{collection_name}" no existe'
                }
            
            info = self.client.get_collection(collection_name=collection_name)
            
            return {
                'success': True,
                'count': info.points_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }