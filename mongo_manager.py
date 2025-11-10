"""
MongoDB Manager para RAG System
Gestiona caché, historial conversacional y configuración de categorías
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json
from bson import ObjectId


class MongoManager:
    """Gestor centralizado de MongoDB para el sistema RAG."""
    
    def __init__(self, mongo_uri: str = None, database_name: str = "rag_system"):
        """
        Inicializa la conexión con MongoDB.
        
        Args:
            mongo_uri: URI de conexión a MongoDB (si no se proporciona, usa MONGO_URI del .env)
            database_name: Nombre de la base de datos
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        if not self.mongo_uri:
            raise ValueError("MONGO_URI no está configurada en las variables de entorno")
        
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()
        self._setup_collections()
    
    def _connect(self):
        """Establece la conexión con MongoDB."""
        try:
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            print(f"✅ Conectado exitosamente a MongoDB: {self.database_name}")
        except ConnectionFailure as e:
            print(f"❌ Error al conectar con MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Configura las colecciones e índices necesarios."""
        try:
            # Colección de caché de respuestas
            self.cache_collection = self.db["answer_cache"]
            self.cache_collection.create_index([("cache_key", ASCENDING)], unique=True)
            self.cache_collection.create_index([("created_at", DESCENDING)])
            self.cache_collection.create_index([("category", ASCENDING)])
            
            # Colección de historial conversacional
            self.conversations_collection = self.db["conversations"]
            self.conversations_collection.create_index([("session_id", ASCENDING)])
            self.conversations_collection.create_index([("updated_at", DESCENDING)])
            
            # Colección de configuración de categorías
            self.categories_collection = self.db["categories"]
            self.categories_collection.create_index([("name", ASCENDING)], unique=True)
            
            # Colección de métricas y estadísticas
            self.metrics_collection = self.db["metrics"]
            self.metrics_collection.create_index([("timestamp", DESCENDING)])
            self.metrics_collection.create_index([("type", ASCENDING)])
            
            print("✅ Colecciones e índices configurados correctamente")
        except Exception as e:
            print(f"⚠️ Error al configurar colecciones: {e}")
    
    # ==================== CACHÉ DE RESPUESTAS ====================
    
    def get_cached_answer(self, cache_key: str) -> Optional[Dict]:
        """
        Obtiene una respuesta del caché.
        
        Args:
            cache_key: Clave única del caché
            
        Returns:
            Dict con la respuesta cacheada o None si no existe
        """
        try:
            cached = self.cache_collection.find_one({"cache_key": cache_key})
            
            if cached:
                # Actualizar contador de hits
                self.cache_collection.update_one(
                    {"cache_key": cache_key},
                    {
                        "$inc": {"hit_count": 1},
                        "$set": {"last_accessed": datetime.utcnow()}
                    }
                )
                
                print(f"⚡ Respuesta recuperada del caché MongoDB (hits: {cached.get('hit_count', 0) + 1})")
                
                # Remover campos internos de MongoDB
                cached.pop('_id', None)
                cached.pop('created_at', None)
                cached.pop('last_accessed', None)
                cached.pop('hit_count', None)
                cached.pop('cache_key', None)
                
                return cached
            
            return None
        except Exception as e:
            print(f"⚠️ Error al obtener del caché: {e}")
            return None
    
    def set_cached_answer(self, cache_key: str, answer_data: Dict):
        """
        Guarda una respuesta en el caché.
        
        Args:
            cache_key: Clave única del caché
            answer_data: Datos de la respuesta a cachear
        """
        try:
            self.cache_collection.update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        **answer_data,
                        "cache_key": cache_key,
                        "created_at": datetime.utcnow(),
                        "last_accessed": datetime.utcnow(),
                        "hit_count": 0
                    }
                },
                upsert=True
            )
            print(f"💾 Respuesta guardada en caché MongoDB")
            
            # Registrar métrica
            self._log_metric("cache_write", {"cache_key": cache_key})
        except Exception as e:
            print(f"⚠️ Error al guardar en caché: {e}")
    
    def clear_cache(self, category: Optional[str] = None, older_than_days: Optional[int] = None):
        """
        Limpia el caché según criterios.
        
        Args:
            category: Si se especifica, solo limpia esa categoría
            older_than_days: Si se especifica, solo limpia entradas más antiguas
        """
        try:
            query = {}
            
            if category:
                query["category"] = category
            
            if older_than_days:
                cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
                query["created_at"] = {"$lt": cutoff_date}
            
            result = self.cache_collection.delete_many(query)
            print(f"🗑️ Caché limpiado: {result.deleted_count} entradas eliminadas")
            
            return result.deleted_count
        except Exception as e:
            print(f"⚠️ Error al limpiar caché: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Dict con estadísticas del caché
        """
        try:
            total_entries = self.cache_collection.count_documents({})
            
            # Estadísticas por categoría
            category_stats = list(self.cache_collection.aggregate([
                {
                    "$group": {
                        "_id": "$category",
                        "count": {"$sum": 1},
                        "total_hits": {"$sum": "$hit_count"}
                    }
                }
            ]))
            
            # Top 10 más accedidas
            top_cached = list(self.cache_collection.find(
                {},
                {"question": 1, "category": 1, "hit_count": 1, "_id": 0}
            ).sort("hit_count", DESCENDING).limit(10))
            
            return {
                "total_entries": total_entries,
                "categories": category_stats,
                "top_cached": top_cached
            }
        except Exception as e:
            print(f"⚠️ Error al obtener estadísticas: {e}")
            return {}
    
    # ==================== HISTORIAL CONVERSACIONAL ====================
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene el historial de conversación de una sesión.
        
        Args:
            session_id: ID de la sesión
            limit: Número máximo de mensajes a retornar
            
        Returns:
            Lista de mensajes ordenados cronológicamente
        """
        try:
            conv = self.conversations_collection.find_one({"session_id": session_id})
            
            if conv and "messages" in conv:
                messages = conv["messages"]
                # Retornar los últimos N mensajes
                return messages[-limit:] if len(messages) > limit else messages
            
            return []
        except Exception as e:
            print(f"⚠️ Error al obtener historial: {e}")
            return []
    
    def save_conversation_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Guarda un mensaje en el historial conversacional.
        
        Args:
            session_id: ID de la sesión
            role: Rol del mensaje (user/assistant)
            content: Contenido del mensaje
            metadata: Metadatos adicionales (categoría, formato, etc.)
        """
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            
            if metadata:
                message["metadata"] = metadata
            
            self.conversations_collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": message},
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "message_count": {"$size": "$messages"}
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            
            # Limitar historial a 100 mensajes por sesión
            self.conversations_collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [],
                            "$slice": -100  # Mantener solo los últimos 100
                        }
                    }
                }
            )
            
        except Exception as e:
            print(f"⚠️ Error al guardar mensaje: {e}")
    
    def clear_conversation(self, session_id: str):
        """
        Limpia el historial de una sesión específica.
        
        Args:
            session_id: ID de la sesión a limpiar
        """
        try:
            result = self.conversations_collection.delete_one({"session_id": session_id})
            print(f"🗑️ Historial de sesión {session_id} eliminado")
            return result.deleted_count > 0
        except Exception as e:
            print(f"⚠️ Error al limpiar conversación: {e}")
            return False
    
    def get_active_sessions(self, hours: int = 24) -> List[Dict]:
        """
        Obtiene sesiones activas en las últimas N horas.
        
        Args:
            hours: Número de horas para considerar una sesión activa
            
        Returns:
            Lista de sesiones activas
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            
            sessions = list(self.conversations_collection.find(
                {"updated_at": {"$gte": cutoff_date}},
                {"session_id": 1, "updated_at": 1, "message_count": 1, "_id": 0}
            ).sort("updated_at", DESCENDING))
            
            return sessions
        except Exception as e:
            print(f"⚠️ Error al obtener sesiones activas: {e}")
            return []
    
    # ==================== CONFIGURACIÓN DE CATEGORÍAS ====================
    
    def load_categories_config(self) -> Dict:
        """
        Carga la configuración de todas las categorías desde MongoDB.
        
        Returns:
            Dict con configuración de categorías {nombre: config}
        """
        try:
            categories = {}
            
            for cat in self.categories_collection.find():
                name = cat.pop('name')
                cat.pop('_id', None)
                categories[name] = cat
            
            return categories
        except Exception as e:
            print(f"⚠️ Error al cargar categorías: {e}")
            return {}
    
    def save_category_config(self, name: str, config: Dict):
        """
        Guarda o actualiza la configuración de una categoría.
        
        Args:
            name: Nombre de la categoría
            config: Configuración de la categoría
        """
        try:
            # Preparar datos para guardar
            data_to_save = {**config}
            data_to_save["name"] = name
            data_to_save["updated_at"] = datetime.utcnow()
            
            # Si no tiene created_at, agregarlo
            if "created_at" not in data_to_save:
                data_to_save["created_at"] = datetime.utcnow()
            
            # Usar replace_one para evitar conflictos con $setOnInsert
            self.categories_collection.replace_one(
                {"name": name},
                data_to_save,
                upsert=True
            )
            print(f"💾 Configuración de categoría '{name}' guardada")
        except Exception as e:
            print(f"⚠️ Error al guardar categoría: {e}")
    
    def get_category_config(self, name: str) -> Optional[Dict]:
        """
        Obtiene la configuración de una categoría específica.
        
        Args:
            name: Nombre de la categoría
            
        Returns:
            Dict con la configuración o None si no existe
        """
        try:
            cat = self.categories_collection.find_one({"name": name})
            
            if cat:
                cat.pop('_id', None)
                return cat
            
            return None
        except Exception as e:
            print(f"⚠️ Error al obtener categoría: {e}")
            return None
    
    def delete_category_config(self, name: str) -> bool:
        """
        Elimina la configuración de una categoría.
        
        Args:
            name: Nombre de la categoría
            
        Returns:
            True si se eliminó, False en caso contrario
        """
        try:
            result = self.categories_collection.delete_one({"name": name})
            return result.deleted_count > 0
        except Exception as e:
            print(f"⚠️ Error al eliminar categoría: {e}")
            return False
    
    # ==================== MÉTRICAS Y LOGGING ====================
    
    def _log_metric(self, metric_type: str, data: Dict):
        """
        Registra una métrica en la base de datos.
        
        Args:
            metric_type: Tipo de métrica (cache_hit, cache_write, query, etc.)
            data: Datos de la métrica
        """
        try:
            self.metrics_collection.insert_one({
                "type": metric_type,
                "timestamp": datetime.utcnow(),
                "data": data
            })
        except Exception as e:
            # No imprimir error para no saturar logs
            pass
    
    def get_metrics(self, metric_type: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """
        Obtiene métricas del sistema.
        
        Args:
            metric_type: Tipo de métrica a filtrar (opcional)
            hours: Número de horas hacia atrás
            
        Returns:
            Lista de métricas
        """
        try:
            query = {"timestamp": {"$gte": datetime.utcnow() - timedelta(hours=hours)}}
            
            if metric_type:
                query["type"] = metric_type
            
            metrics = list(self.metrics_collection.find(
                query,
                {"_id": 0}
            ).sort("timestamp", DESCENDING).limit(1000))
            
            return metrics
        except Exception as e:
            print(f"⚠️ Error al obtener métricas: {e}")
            return []
    
    # ==================== UTILIDADES ====================
    
    def health_check(self) -> Dict:
        """
        Verifica el estado de salud de MongoDB.
        
        Returns:
            Dict con información del estado
        """
        try:
            # Verificar conexión
            self.client.admin.command('ping')
            
            # Obtener estadísticas
            stats = {
                "status": "healthy",
                "database": self.database_name,
                "collections": {
                    "cache": self.cache_collection.count_documents({}),
                    "conversations": self.conversations_collection.count_documents({}),
                    "categories": self.categories_collection.count_documents({}),
                    "metrics": self.metrics_collection.count_documents({})
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return stats
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def close(self):
        """Cierra la conexión con MongoDB."""
        if self.client:
            self.client.close()
            print("🔌 Conexión con MongoDB cerrada")


# Instancia global del gestor de MongoDB
_mongo_manager: Optional[MongoManager] = None


def get_mongo_manager() -> MongoManager:
    """
    Obtiene la instancia global del gestor de MongoDB (patrón Singleton).
    
    Returns:
        Instancia de MongoManager
    """
    global _mongo_manager
    
    if _mongo_manager is None:
        _mongo_manager = MongoManager()
    
    return _mongo_manager


def close_mongo_connection():
    """Cierra la conexión global de MongoDB."""
    global _mongo_manager
    
    if _mongo_manager:
        _mongo_manager.close()
        _mongo_manager = None
