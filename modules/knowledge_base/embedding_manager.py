import os
from openai import OpenAI
from typing import List, Dict, Any
import tiktoken

class EmbeddingManager:
    """Gestor de embeddings usando OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY debe estar configurado en .env")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-large"
        self.dimensions = 3072
        
        # Encoding para contar tokens
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except:
            # Fallback a cl100k_base si el modelo no está disponible
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con OpenAI"""
        try:
            # Generar un embedding de prueba
            response = self.client.embeddings.create(
                input="test",
                model=self.model,
                dimensions=self.dimensions
            )
            
            return {
                'success': True,
                'message': 'Conexión exitosa con OpenAI',
                'model': self.model,
                'dimensions': len(response.data[0].embedding)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def count_tokens(self, text: str) -> int:
        """Contar tokens en un texto"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            print(f"Error contando tokens: {str(e)}")
            # Estimación aproximada: 1 token ≈ 4 caracteres
            return len(text) // 4
    
    def generate_embedding(self, text: str) -> Dict[str, Any]:
        """Generar embedding para un texto"""
        try:
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'El texto no puede estar vacío'
                }
            
            # Contar tokens
            token_count = self.count_tokens(text)
            
            # Límite de OpenAI es ~8191 tokens para text-embedding-3-large
            if token_count > 8000:
                return {
                    'success': False,
                    'error': f'El texto es muy largo ({token_count} tokens). Máximo: 8000 tokens'
                }
            
            # Generar embedding
            response = self.client.embeddings.create(
                input=text,
                model=self.model,
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            
            return {
                'success': True,
                'embedding': embedding,
                'token_count': token_count,
                'dimensions': len(embedding)
            }
            
        except Exception as e:
            print(f"Error generando embedding: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_embeddings_batch(self, texts: List[str]) -> Dict[str, Any]:
        """Generar embeddings para múltiples textos en batch"""
        try:
            if not texts:
                return {
                    'success': False,
                    'error': 'La lista de textos no puede estar vacía'
                }
            
            # Filtrar textos vacíos
            valid_texts = [text for text in texts if text and text.strip()]
            
            if not valid_texts:
                return {
                    'success': False,
                    'error': 'Todos los textos están vacíos'
                }
            
            # OpenAI permite hasta 2048 textos por request
            if len(valid_texts) > 2048:
                return {
                    'success': False,
                    'error': f'Demasiados textos ({len(valid_texts)}). Máximo: 2048'
                }
            
            # Verificar tokens de cada texto
            total_tokens = 0
            for text in valid_texts:
                tokens = self.count_tokens(text)
                if tokens > 8000:
                    return {
                        'success': False,
                        'error': f'Un texto tiene {tokens} tokens. Máximo: 8000 tokens por texto'
                    }
                total_tokens += tokens
            
            # Generar embeddings
            response = self.client.embeddings.create(
                input=valid_texts,
                model=self.model,
                dimensions=self.dimensions
            )
            
            # Extraer embeddings en el mismo orden
            embeddings = [item.embedding for item in response.data]
            
            return {
                'success': True,
                'embeddings': embeddings,
                'count': len(embeddings),
                'total_tokens': total_tokens,
                'dimensions': len(embeddings[0]) if embeddings else 0
            }
            
        except Exception as e:
            print(f"Error generando embeddings batch: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def chunk_text(self, text: str, max_tokens: int = 6000, overlap: int = 200) -> List[str]:
        """
        Dividir texto largo en chunks con overlap
        
        Args:
            text: Texto a dividir
            max_tokens: Máximo de tokens por chunk
            overlap: Tokens de overlap entre chunks
        
        Returns:
            Lista de chunks de texto
        """
        try:
            # Tokenizar el texto completo
            tokens = self.encoding.encode(text)
            
            # Si el texto cabe en un solo chunk, retornarlo
            if len(tokens) <= max_tokens:
                return [text]
            
            # Dividir en chunks con overlap
            chunks = []
            start = 0
            
            while start < len(tokens):
                # Definir el fin del chunk
                end = start + max_tokens
                
                # Extraer tokens del chunk
                chunk_tokens = tokens[start:end]
                
                # Decodificar a texto
                chunk_text = self.encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
                
                # Mover el inicio considerando el overlap
                start = end - overlap
                
                # Si el siguiente chunk sería muy pequeño, mejor terminamos
                if len(tokens) - start < overlap:
                    break
            
            return chunks
            
        except Exception as e:
            print(f"Error dividiendo texto: {str(e)}")
            # Fallback: dividir por caracteres
            chunk_size = max_tokens * 4  # Aproximación
            overlap_chars = overlap * 4
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start = end - overlap_chars
                
                if len(text) - start < overlap_chars:
                    break
            
            return chunks
    
    def estimate_cost(self, token_count: int) -> Dict[str, Any]:
        """
        Estimar costo de generación de embeddings
        
        Precios (a dic 2024):
        - text-embedding-3-large: $0.13 por 1M tokens
        """
        try:
            cost_per_million = 0.13
            cost = (token_count / 1_000_000) * cost_per_million
            
            return {
                'success': True,
                'tokens': token_count,
                'cost_usd': round(cost, 6),
                'cost_formatted': f'${cost:.6f} USD'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo actual"""
        return {
            'model': self.model,
            'dimensions': self.dimensions,
            'max_tokens': 8191,
            'cost_per_million_tokens': 0.13,
            'description': 'OpenAI text-embedding-3-large - Embeddings de alta calidad'
        }