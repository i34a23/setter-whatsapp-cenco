import pandas as pd
import os
from datetime import datetime
import chardet

class FileProcessor:
    """Procesa archivos CSV, Excel y similares"""
    
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'tsv'}
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileProcessor.ALLOWED_EXTENSIONS
    
    @staticmethod
    def detect_encoding(file_path):
        """Detecta el encoding de un archivo"""
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding']
    
    @staticmethod
    def read_file(file_path):
        """Lee un archivo y retorna un DataFrame de pandas"""
        ext = file_path.rsplit('.', 1)[1].lower()
        
        try:
            if ext == 'csv':
                # Detectar encoding
                encoding = FileProcessor.detect_encoding(file_path)
                # Intentar con diferentes delimitadores
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                except:
                    df = pd.read_csv(file_path, encoding=encoding, delimiter=';')
            
            elif ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            
            elif ext == 'tsv':
                encoding = FileProcessor.detect_encoding(file_path)
                df = pd.read_csv(file_path, encoding=encoding, delimiter='\t')
            
            else:
                raise ValueError(f"Formato de archivo no soportado: {ext}")
            
            return df
        
        except Exception as e:
            raise Exception(f"Error al leer el archivo: {str(e)}")
    
    @staticmethod
    def get_columns(file_path):
        """Obtiene las columnas del archivo"""
        df = FileProcessor.read_file(file_path)
        return df.columns.tolist()
    
    @staticmethod
    def get_preview(file_path, rows=5):
        """Obtiene una vista previa del archivo"""
        df = FileProcessor.read_file(file_path)
        preview = df.head(rows).to_dict('records')
        return {
            'columns': df.columns.tolist(),
            'rows': preview,
            'total_rows': len(df)
        }
    
    @staticmethod
    def normalize_column_name(name):
        """Normaliza el nombre de una columna para comparación"""
        if not name:
            return ""
        return str(name).lower().strip()
    
    @staticmethod
    def suggest_mapping(file_columns, target_fields):
        """
        Sugiere un mapeo automático entre columnas del archivo y campos objetivo
        
        Args:
            file_columns: Lista de columnas del archivo
            target_fields: Diccionario con campos objetivo y sus sinónimos
            
        Returns:
            Diccionario con mapeo sugerido
        """
        mapping = {}
        
        # Normalizar columnas del archivo
        normalized_file_cols = {
            FileProcessor.normalize_column_name(col): col 
            for col in file_columns
        }
        
        for target_field, synonyms in target_fields.items():
            for synonym in synonyms:
                normalized_synonym = FileProcessor.normalize_column_name(synonym)
                if normalized_synonym in normalized_file_cols:
                    mapping[target_field] = normalized_file_cols[normalized_synonym]
                    break
        
        return mapping
    
    @staticmethod
    def process_and_map(file_path, column_mapping):
        """
        Procesa el archivo y mapea las columnas según el mapeo proporcionado
        
        Args:
            file_path: Ruta al archivo
            column_mapping: Diccionario {campo_destino: columna_origen}
            
        Returns:
            Lista de diccionarios con los datos mapeados
        """
        df = FileProcessor.read_file(file_path)
        
        # Crear DataFrame con columnas mapeadas
        mapped_data = []
        
        for _, row in df.iterrows():
            record = {}
            for target_field, source_column in column_mapping.items():
                if source_column and source_column in df.columns:
                    value = row[source_column]
                    # Convertir NaN y valores problemáticos a None
                    if pd.isna(value):
                        record[target_field] = None
                    elif isinstance(value, float) and (value != value):  # NaN check
                        record[target_field] = None
                    else:
                        # Convertir a tipo nativo de Python
                        if isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[target_field] = str(value)
                        elif isinstance(value, (int, float)):
                            record[target_field] = value if not pd.isna(value) else None
                        else:
                            record[target_field] = str(value) if value is not None else None
                else:
                    record[target_field] = None
            
            # Agregar columnas adicionales que no fueron mapeadas
            additional_data = {}
            for col in df.columns:
                if col not in column_mapping.values():
                    value = row[col]
                    if not pd.isna(value):
                        # Convertir a tipo JSON-serializable
                        if isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            additional_data[col] = str(value)
                        elif isinstance(value, (int, float)):
                            additional_data[col] = value if not pd.isna(value) else None
                        else:
                            additional_data[col] = str(value) if value is not None else None
            
            if additional_data:
                record['datos_adicionales'] = additional_data
            
            mapped_data.append(record)
        
        return mapped_data
