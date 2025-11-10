# 🚀 Inicio Rápido - Sistema RAG con MongoDB

## ⚡ Quick Start (3 pasos)

### 1️⃣ Migrar a MongoDB

```bash
python migrate_to_mongo.py
```

### 2️⃣ Reiniciar Servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ Verificar

```bash
# Opción A: Con script helper
./mongodb_helper.sh status

# Opción B: Manual
curl http://localhost:8000/mongodb/health
```

**¡Listo! 🎉** El sistema ahora usa MongoDB.

---

## 📚 Documentación Completa

| Documento                                              | Descripción                    |
| ------------------------------------------------------ | ------------------------------ |
| **[RESUMEN_MONGODB.md](RESUMEN_MONGODB.md)**           | 📊 Resumen ejecutivo completo  |
| **[GUIA_MIGRACION_MONGO.md](GUIA_MIGRACION_MONGO.md)** | 📖 Guía detallada de migración |
| **[CHECKLIST_MIGRACION.md](CHECKLIST_MIGRACION.md)**   | ✅ Checklist paso a paso       |

---

## 🛠️ Script Helper

El script `mongodb_helper.sh` facilita todas las operaciones:

```bash
# Ver comandos disponibles
./mongodb_helper.sh help

# Verificar estado del sistema
./mongodb_helper.sh status

# Ver estadísticas del caché
./mongodb_helper.sh cache-stats

# Limpiar caché de una categoría
./mongodb_helper.sh cache-clear-cat geomecanica

# Ver conversaciones activas
./mongodb_helper.sh conversations

# Ejecutar pruebas
./mongodb_helper.sh test
```

---

## 🎯 Nuevos Endpoints

### Caché

```bash
GET    /cache/stats                    # Estadísticas
DELETE /cache/clear                    # Limpiar todo
DELETE /cache/clear/{category}         # Por categoría
DELETE /cache/clear/older-than/{days}  # Por fecha
```

### MongoDB

```bash
GET /mongodb/health     # Salud del sistema
GET /mongodb/metrics    # Métricas de uso
```

### Conversaciones

```bash
GET    /conversations              # Listar
GET    /conversations/{session}    # Obtener
DELETE /conversations/{session}    # Limpiar una
DELETE /conversations              # Limpiar todas
```

---

## 📊 ¿Qué cambió?

### Antes

```python
# Caché en memoria (se pierde al reiniciar)
answer_cache: Dict[str, dict] = {}
conversation_history: Dict[str, List[dict]] = {}
```

### Después

```python
# Caché persistente en MongoDB
from mongo_manager import get_mongo_manager
mongo = get_mongo_manager()

# Todo se guarda en MongoDB automáticamente
```

### Beneficios

- ✅ Caché sobrevive a reinicios
- ✅ Compartido entre múltiples instancias
- ✅ Sin límite de 100 entradas
- ✅ Métricas detalladas de uso
- ✅ Historial conversacional persistente

---

## 🧪 Probar el Sistema

### Prueba Automática

```bash
python test_mongodb_migration.py
```

### Prueba Manual

```bash
# 1. Verificar MongoDB
curl http://localhost:8000/mongodb/health

# 2. Hacer una pregunta
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
  }'

# 3. Verificar que se guardó en caché
curl http://localhost:8000/cache/stats

# 4. Hacer la misma pregunta (debería ser instantánea)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
  }'
```

---

## 🔧 Troubleshooting

### Error: "MONGO_URI no está configurada"

```bash
# Verificar .env
cat .env | grep MONGO_URI

# Si no existe, agregarlo
echo 'MONGO_URI=mongodb+srv://...' >> .env
```

### Error: "ServerSelectionTimeoutError"

1. Verifica que la IP está en whitelist de MongoDB Atlas
2. Verifica las credenciales en MONGO_URI
3. Verifica conectividad de red

### El caché no se está usando

```bash
# Ver estadísticas
./mongodb_helper.sh cache-stats

# Verificar logs del servidor para errores
```

---

## 📞 Comandos Útiles

```bash
# Estado general
./mongodb_helper.sh status

# Limpiezas
./mongodb_helper.sh cache-clear               # Caché completo
./mongodb_helper.sh cache-clear-cat compliance # Por categoría
./mongodb_helper.sh cache-clear-old 30        # Más de 30 días
./mongodb_helper.sh conversations-clear       # Conversaciones

# Monitoreo
./mongodb_helper.sh mongodb-health           # Salud
./mongodb_helper.sh mongodb-metrics          # Métricas
./mongodb_helper.sh cache-stats              # Estadísticas

# Testing
./mongodb_helper.sh test                     # Suite completa
./mongodb_helper.sh test-question "..."      # Pregunta específica
```

---

## 📈 Mejoras Clave

| Métrica       | Antes      | Después      | Mejora |
| ------------- | ---------- | ------------ | ------ |
| Persistencia  | ❌         | ✅           | ∞      |
| Límite Caché  | 100        | Ilimitado    | 100x+  |
| Escalabilidad | 1 servidor | N servidores | Nx     |
| Hit Rate      | ~40%       | ~70%\*       | +30%   |
| Historial     | Temporal   | Persistente  | ∞      |

_\* Estimado_

---

## ✅ Verificación Rápida

```bash
# ¿Está todo bien?
./mongodb_helper.sh status

# Salida esperada:
# ✅ Servidor corriendo en http://localhost:8000
# ✅ MongoDB está saludable
# {
#   "status": "healthy",
#   "database": "rag_system",
#   "collections": {
#     "cache": 0,
#     "conversations": 0,
#     "categories": 2,
#     "metrics": 0
#   }
# }
```

---

## 🎉 ¡Listo!

El sistema ahora está ejecutándose con MongoDB. Todas las consultas se cachean automáticamente y el historial conversacional se mantiene entre sesiones.

### Próximos pasos sugeridos:

1. ✅ Hacer algunas preguntas de prueba
2. ✅ Verificar que el caché funciona
3. ✅ Probar conversaciones con contexto
4. ✅ Monitorear métricas

---

**Versión**: 5.0 - MongoDB Integration
**Fecha**: 10 de noviembre de 2025
**Estado**: ✅ OPERACIONAL
