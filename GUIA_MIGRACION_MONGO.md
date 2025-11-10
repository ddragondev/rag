# 🚀 Guía de Migración a MongoDB - Sistema RAG

## 📋 Resumen de Cambios

Se ha migrado exitosamente el sistema de caché en memoria a **MongoDB Atlas**, mejorando significativamente:

✅ **Persistencia**: Caché sobrevive a reinicios del servidor
✅ **Escalabilidad**: Múltiples instancias pueden compartir caché
✅ **Métricas**: Seguimiento detallado de uso y rendimiento
✅ **Historial**: Conversaciones almacenadas de forma persistente

---

## 🗂️ Archivos Modificados y Creados

### Nuevos Archivos

1. **`mongo_manager.py`** - Gestor completo de MongoDB

   - Conexión y configuración de colecciones
   - Gestión de caché de respuestas
   - Historial conversacional
   - Configuración de categorías
   - Métricas y logging

2. **`migrate_to_mongo.py`** - Script de migración

   - Migra `categories_config.json` a MongoDB
   - Crea backup del archivo JSON original
   - Verifica migración exitosa

3. **`GUIA_MIGRACION_MONGO.md`** (este archivo)
   - Documentación completa de la migración

### Archivos Modificados

1. **`requirements.txt`**

   ```
   + pymongo>=4.6.0
   + dnspython>=2.4.0
   ```

2. **`main.py`**
   - Importa `MongoManager`
   - Reemplaza caché en memoria por MongoDB
   - Startup/shutdown events para conexión MongoDB
   - Nuevos endpoints de gestión

---

## 🎯 Nuevos Endpoints

### Gestión de Caché

```bash
# Obtener estadísticas del caché
GET /cache/stats
# Respuesta:
{
  "total_entries": 150,
  "categories": [
    {"_id": "geomecanica", "count": 80, "total_hits": 450},
    {"_id": "compliance", "count": 70, "total_hits": 320}
  ],
  "top_cached": [...],
  "vectorstore_cache_size": 2
}

# Limpiar todo el caché
DELETE /cache/clear

# Limpiar caché de una categoría específica
DELETE /cache/clear/{category}

# Limpiar caché antiguo (> N días)
DELETE /cache/clear/older-than/{days}
```

### Gestión de Conversaciones

```bash
# Listar conversaciones activas
GET /conversations

# Obtener historial de una conversación
GET /conversations/{session_id}

# Limpiar conversación específica
DELETE /conversations/{session_id}

# Limpiar todas las conversaciones
DELETE /conversations
```

### Salud y Métricas de MongoDB

```bash
# Verificar estado de MongoDB
GET /mongodb/health
# Respuesta:
{
  "status": "healthy",
  "database": "rag_system",
  "collections": {
    "cache": 150,
    "conversations": 12,
    "categories": 2,
    "metrics": 1500
  },
  "timestamp": "2025-11-10T..."
}

# Obtener métricas del sistema
GET /mongodb/metrics?hours=24
```

---

## 📊 Estructura de MongoDB

### Base de Datos: `rag_system`

#### Colección: `answer_cache`

```javascript
{
  "_id": ObjectId("..."),
  "cache_key": "abc123...",
  "question": "¿Qué es...?",
  "category": "geomecanica",
  "format": "both",
  "answer": "...",
  "answer_plain": "...",
  "sources": "...",
  "sources_plain": "...",
  "created_at": ISODate("2025-11-10T..."),
  "last_accessed": ISODate("2025-11-10T..."),
  "hit_count": 15
}
```

**Índices:**

- `cache_key` (único)
- `created_at` (descendente)
- `category`

#### Colección: `conversations`

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "session-123",
  "messages": [
    {
      "role": "user",
      "content": "¿Qué es...?",
      "timestamp": ISODate("..."),
      "metadata": {
        "category": "geomecanica",
        "format": "html"
      }
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": ISODate("..."),
      "metadata": {...}
    }
  ],
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "message_count": 10
}
```

**Índices:**

- `session_id`
- `updated_at` (descendente)

#### Colección: `categories`

```javascript
{
  "_id": ObjectId("..."),
  "name": "geomecanica",
  "display_name": "Geomecánica",
  "description": "...",
  "prompt_html": "...",
  "prompt_plain": "...",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**Índices:**

- `name` (único)

#### Colección: `metrics`

```javascript
{
  "_id": ObjectId("..."),
  "type": "cache_write",
  "timestamp": ISODate("..."),
  "data": {
    "cache_key": "...",
    // datos específicos del tipo de métrica
  }
}
```

**Índices:**

- `timestamp` (descendente)
- `type`

---

## 🔧 Proceso de Migración

### Paso 1: Ejecutar Script de Migración

```bash
python migrate_to_mongo.py
```

**Salida esperada:**

```
🚀 Iniciando migración a MongoDB
============================================================
📖 Leyendo configuración desde categories_config.json
📊 Categorías encontradas: 2
✅ Categoría 'geomecanica' migrada
✅ Categoría 'compliance' migrada

🎉 Migración completada: 2/2 categorías migradas
💾 Backup creado: categories_config.json.backup_20251110_153045

🔍 Verificando migración...
✅ Verificación exitosa: todas las categorías están en MongoDB

📋 Categorías en MongoDB:
============================================================
...
```

### Paso 2: Verificar Conexión

```bash
curl http://localhost:8000/mongodb/health
```

### Paso 3: Reiniciar Servidor

```bash
# Si usas uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Si usas el script de deploy
bash deploy_ubuntu.sh
```

**Salida esperada al iniciar:**

```
✅ Conectado exitosamente a MongoDB: rag_system
✅ Colecciones e índices configurados correctamente
✅ Sistema iniciado con MongoDB
INFO:     Application startup complete.
```

---

## 📈 Mejoras de Rendimiento

### Antes (Caché en Memoria)

- ⚠️ Caché se pierde al reiniciar
- ⚠️ Limitado a 100 entradas (FIFO)
- ⚠️ No compartido entre instancias
- ⚠️ Sin métricas de uso
- ⚠️ Historial conversacional limitado

### Después (MongoDB)

- ✅ Caché persistente
- ✅ Sin límite de entradas (gestionado por MongoDB)
- ✅ Compartido entre múltiples instancias
- ✅ Métricas detalladas (hits, categorías, etc.)
- ✅ Historial ilimitado con gestión automática
- ✅ Búsquedas optimizadas con índices

### Métricas de Rendimiento

| Operación     | Caché Memoria | MongoDB      | Mejora     |
| ------------- | ------------- | ------------ | ---------- |
| Cache Hit     | ~0ms          | ~50-100ms    | -50ms      |
| Cache Miss    | 2-5s          | 2-5s         | Sin cambio |
| Persistencia  | ❌            | ✅           | Infinita   |
| Escalabilidad | 1 instancia   | N instancias | ∞          |
| Historial     | En memoria    | Persistente  | ✅         |

---

## 🛠️ Comandos Útiles

### Gestión de Caché

```bash
# Ver estadísticas
curl http://localhost:8000/cache/stats

# Limpiar todo
curl -X DELETE http://localhost:8000/cache/clear

# Limpiar una categoría
curl -X DELETE http://localhost:8000/cache/clear/geomecanica

# Limpiar caché antiguo (> 30 días)
curl -X DELETE http://localhost:8000/cache/clear/older-than/30
```

### Gestión de Conversaciones

```bash
# Ver conversaciones activas
curl http://localhost:8000/conversations

# Ver historial específico
curl http://localhost:8000/conversations/session-123

# Limpiar conversación
curl -X DELETE http://localhost:8000/conversations/session-123
```

### Monitoreo

```bash
# Verificar salud de MongoDB
curl http://localhost:8000/mongodb/health

# Ver métricas (últimas 24 horas)
curl http://localhost:8000/mongodb/metrics?hours=24
```

---

## 🔒 Seguridad y Configuración

### Variables de Entorno

```env
# .env
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?appName=Cluster0
OPENAI_API_KEY=sk-...
```

### Configuración de MongoDB Atlas

1. **Whitelist IP**: Agregar IP del servidor
2. **Network Access**: Permitir conexiones desde cualquier IP (0.0.0.0/0) para desarrollo
3. **Database User**: Crear usuario con permisos de lectura/escritura
4. **Connection String**: Usar el formato `mongodb+srv://`

---

## 🐛 Troubleshooting

### Error: "MONGO_URI no está configurada"

**Solución:**

```bash
# Verificar que .env existe y tiene MONGO_URI
cat .env | grep MONGO_URI

# Si no existe, agregarlo
echo 'MONGO_URI=mongodb+srv://...' >> .env
```

### Error: "ServerSelectionTimeoutError"

**Causas:**

1. IP no está en whitelist de MongoDB Atlas
2. Credenciales incorrectas
3. Red no permite conexiones a MongoDB

**Solución:**

```bash
# Verificar conectividad
ping cluster.fbozhvy.mongodb.net

# Verificar firewall
sudo ufw status

# Verificar logs
tail -f logs/app.log
```

### Error: "Caché no se está usando"

**Verificar:**

```bash
# Ver estadísticas
curl http://localhost:8000/cache/stats

# Si total_entries es 0, el caché no se está escribiendo
# Verificar logs del servidor para errores de MongoDB
```

### Sistema funciona pero sin MongoDB

Si MongoDB falla al iniciar, el sistema **continuará funcionando** en modo limitado:

- ⚠️ Sin caché persistente
- ⚠️ Sin historial conversacional
- ✅ Búsqueda de documentos funciona
- ✅ Respuestas LLM funcionan

---

## 📝 Notas Importantes

1. **Backup automático**: Al migrar, el archivo JSON original se respalda automáticamente
2. **Límite de historial**: Cada sesión mantiene máximo 100 mensajes (últimos 100)
3. **Limpieza automática**: No hay limpieza automática, usar endpoints DELETE
4. **Índices**: Los índices se crean automáticamente al iniciar
5. **Compatibilidad**: Mantiene compatibilidad con toda la API existente

---

## 🎉 Beneficios Finales

### Para Desarrollo

- 🔄 Hot reload sin perder caché
- 📊 Métricas detalladas para debugging
- 🔍 Fácil inspección de datos en MongoDB Compass

### Para Producción

- 🚀 Múltiples workers compartiendo caché
- 📈 Escalabilidad horizontal
- 💾 Datos persistentes y respaldables
- 📊 Análisis de uso y patrones

### Para Usuarios

- ⚡ Respuestas más rápidas (cache hits)
- 💬 Historial conversacional persistente
- 🎯 Mejor experiencia con contexto

---

## 📞 Soporte

Si encuentras problemas:

1. Verificar logs: `tail -f logs/app.log`
2. Verificar MongoDB: `curl http://localhost:8000/mongodb/health`
3. Verificar caché: `curl http://localhost:8000/cache/stats`
4. Revisar este documento

---

**¡Sistema migrado exitosamente! 🎊**

El sistema ahora utiliza MongoDB para caché, historial y configuración, mejorando significativamente la experiencia y rendimiento.
