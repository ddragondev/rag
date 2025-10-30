# ✅ Resumen: Normalización de Categorías

## 🎯 Problema Resuelto

**Antes:** Los usuarios debían escribir exactamente el nombre de la carpeta (sin tildes, minúsculas).  
**Ahora:** Los usuarios pueden escribir con tildes y mayúsculas, el sistema normaliza automáticamente.

---

## 🚀 Implementación

### Función agregada:

```python
import unicodedata

def normalize_category(category: str) -> str:
    """
    Normaliza categorías:
    - Minúsculas
    - Sin tildes
    """
    category = category.lower()
    category = unicodedata.normalize('NFD', category)
    category = ''.join(char for char in category if unicodedata.category(char) != 'Mn')
    return category
```

### Se aplica en:

- ✅ `POST /ask`
- ✅ `POST /ask-stream`
- ✅ Función `get_or_create_vectorstore()`

---

## 💻 Ejemplos

### Todas estas entradas son válidas:

```bash
# Usuario escribe con tilde y mayúscula
curl -X POST http://localhost:8000/ask \
  -d '{"category": "Geomecánica", "question": "...", "format": "plain"}'

# Usuario escribe todo mayúsculas
curl -X POST http://localhost:8000/ask \
  -d '{"category": "GEOMECÁNICA", "question": "...", "format": "plain"}'

# Usuario escribe sin tilde
curl -X POST http://localhost:8000/ask \
  -d '{"category": "geomecanica", "question": "...", "format": "plain"}'
```

**Todas se normalizan a:** `geomecanica`  
**Buscan en:** `docs/geomecanica/`

---

## 📊 Tabla de Conversiones

| Input Usuario | Normalizado   | Carpeta             |
| ------------- | ------------- | ------------------- |
| `Geomecánica` | `geomecanica` | `docs/geomecanica/` |
| `GEOMECÁNICA` | `geomecanica` | `docs/geomecanica/` |
| `geomecánica` | `geomecanica` | `docs/geomecanica/` |
| `GeoMecánica` | `geomecanica` | `docs/geomecanica/` |
| `Física`      | `fisica`      | `docs/fisica/`      |
| `QUÍMICA`     | `quimica`     | `docs/quimica/`     |

---

## ✨ Beneficios

1. **Mejor UX:** Usuarios escriben naturalmente
2. **Menos errores:** No importa mayúsculas/tildes
3. **Más intuitivo:** "Geomecánica" vs "geomecanica"
4. **Flexible:** Acepta múltiples variaciones

---

## 🧪 Testing

```bash
# Ejecutar pruebas
python test_category_normalization.py
```

**Resultado esperado:**

```
✅ Exitosas: 8/8
   geomecanica     ✅
   Geomecanica     ✅
   GEOMECANICA     ✅
   geomecánica     ✅
   Geomecánica     ✅
   GEOMECÁNICA     ✅
   GeoMecánica     ✅
   geoMECÁNICA     ✅
```

---

## 📁 Archivos Modificados

1. ✅ `main.py` - Función `normalize_category()` agregada
2. ✅ `test_category_normalization.py` - Tests completos
3. ✅ `NORMALIZACION_CATEGORIAS.md` - Documentación completa

---

## 🎯 Uso Recomendado

### Frontend (mostrar bonito):

```javascript
// Mostrar con tildes al usuario
<select>
  <option value="Geomecánica">Geomecánica</option>
  <option value="Física">Física</option>
  <option value="Química">Química</option>
</select>;

// Enviar tal cual, se normaliza en backend
fetch("/ask", {
  body: JSON.stringify({ category: selectedValue }),
});
```

### Carpetas (crear simple):

```bash
# Crear carpetas sin tildes, minúsculas
mkdir docs/geomecanica
mkdir docs/fisica
mkdir docs/quimica
```

---

## 💡 Importante

- ✅ **Carpetas:** minúsculas, sin tildes
- ✅ **API Input:** cualquier formato (se normaliza)
- ✅ **UI Display:** con tildes (más legible)

---

**Estado:** ✅ Implementado  
**Fecha:** 23 de octubre de 2025  
**Impacto:** 🎯 Mejor experiencia de usuario
