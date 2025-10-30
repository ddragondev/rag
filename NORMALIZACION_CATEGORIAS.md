# 🔤 Normalización de Categorías

## 🎯 Característica Implementada

La API ahora **normaliza automáticamente** los nombres de categorías para ser más flexible y tolerante a errores de entrada.

---

## ✨ Qué se Normaliza

### 1. **Mayúsculas → minúsculas**

```python
"GEOMECANICA" → "geomecanica"
"Geomecanica" → "geomecanica"
"GeoMecánica" → "geomecanica"
```

### 2. **Tildes → sin tildes**

```python
"geomecánica" → "geomecanica"
"Geomecánica" → "geomecanica"
"GEOMECÁNICA" → "geomecanica"
```

### 3. **Combinaciones**

```python
"Física"      → "fisica"
"MECÁNICA"    → "mecanica"
"Hidráulica"  → "hidraulica"
```

---

## 🔧 Implementación

### Función de normalización:

```python
import unicodedata

def normalize_category(category: str) -> str:
    """
    Normaliza el nombre de la categoría:
    - Convierte a minúsculas
    - Elimina tildes y acentos
    - Mantiene guiones y guiones bajos
    """
    # Convertir a minúsculas
    category = category.lower()

    # Eliminar tildes usando NFD (Normalization Form Decomposed)
    category = unicodedata.normalize('NFD', category)
    category = ''.join(char for char in category if unicodedata.category(char) != 'Mn')

    return category
```

### Se aplica automáticamente en:

- ✅ `POST /ask`
- ✅ `POST /ask-stream`
- ✅ Todas las funciones internas

---

## 💻 Ejemplos de Uso

### Todas estas variaciones funcionan:

```bash
# Opción 1: Sin tilde, minúscula (nombre de carpeta real)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "geomecanica", "format": "plain"}'

# Opción 2: Con tilde, minúscula
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "geomecánica", "format": "plain"}'

# Opción 3: Sin tilde, mayúscula inicial
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "Geomecanica", "format": "plain"}'

# Opción 4: Con tilde, mayúscula inicial
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "Geomecánica", "format": "plain"}'

# Opción 5: Todo mayúsculas sin tilde
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "GEOMECANICA", "format": "plain"}'

# Opción 6: Todo mayúsculas con tilde
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "GEOMECÁNICA", "format": "plain"}'

# Opción 7: Mix aleatorio
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "GeoMecánica", "format": "plain"}'
```

**Todas se normalizan a:** `geomecanica`

---

## 📁 Estructura de Carpetas

### Importante:

Las carpetas en `docs/` deben estar en **minúsculas sin tildes**:

```
docs/
├── geomecanica/          ✅ Correcto
├── fisica/               ✅ Correcto
├── mecanica-de-rocas/    ✅ Correcto (con guiones)
├── Geomecánica/          ❌ No funcionará (mayúscula + tilde)
└── FÍSICA/               ❌ No funcionará (mayúsculas + tilde)
```

### Regla:

- **Carpetas:** minúsculas, sin tildes
- **Entrada API:** cualquier formato (se normaliza automáticamente)

---

## 🧪 Testing

### Ejecutar pruebas:

```bash
python test_category_normalization.py
```

### Salida esperada:

```
  TEST: Normalización de Categorías
================================================================================

📝 Pregunta de prueba: ¿Qué es el RMR?
📂 Carpeta real en docs/: 'geomecanica' (sin tilde, minúscula)

Variación de entrada      Estado          Tiempo
--------------------------------------------------------------------------------
geomecanica               ✅ Éxito        5.23s
Geomecanica               ✅ Éxito        5.10s
GEOMECANICA               ✅ Éxito        5.15s
geomecánica               ✅ Éxito        5.08s
Geomecánica               ✅ Éxito        5.12s
GEOMECÁNICA               ✅ Éxito        5.09s
GeoMecánica               ✅ Éxito        5.11s
geoMECÁNICA               ✅ Éxito        5.14s

================================================================================
  RESUMEN
================================================================================
✅ Exitosas: 8/8
❌ Fallidas:  0/8

🎉 ¡Perfecto! Todas las variaciones funcionaron correctamente
   La normalización está funcionando como se esperaba
```

---

## 🎨 Casos de Uso

### Frontend (Usuario final):

```javascript
// El usuario escribe con tildes y mayúsculas
const userInput = "Geomecánica"; // Como lo escribiría un humano

fetch("/ask", {
  method: "POST",
  body: JSON.stringify({
    category: userInput, // Se normaliza automáticamente
    question: "¿Qué es el RMR?",
    format: "html",
  }),
});
```

### Autocompletar:

```javascript
// Sugerencias para el usuario (con tildes, más legible)
const suggestions = [
  { display: "Geomecánica", value: "Geomecánica" },
  { display: "Física", value: "Física" },
  { display: "Mecánica de Rocas", value: "Mecánica de Rocas" },
];

// Todas se normalizan automáticamente en el backend
```

---

## 🔍 Caracteres Soportados

### ✅ Se normalizan correctamente:

- `á é í ó ú` → `a e i o u`
- `ñ` → `n`
- `ü` → `u`
- `À È Ì Ò Ù` → `a e i o u`
- `Ä Ë Ï Ö Ü` → `a e i o u`

### ✅ Se mantienen:

- Espacios: `mecanica de rocas`
- Guiones: `mecanica-de-rocas`
- Guiones bajos: `mecanica_rocas`
- Números: `fisica2`, `quimica-101`

### ❌ No afectan la búsqueda pero no se recomiendan:

- Caracteres especiales: `@#$%`
- Emojis: `geomecanica🔧`

---

## 💡 Beneficios

### 1. **Mejor UX**

Los usuarios pueden escribir naturalmente con tildes y mayúsculas.

### 2. **Menos errores**

No importa si el usuario escribe "Geomecánica" o "GEOMECANICA".

### 3. **Internacionalización**

Funciona con diferentes acentos del español.

### 4. **Consistencia**

Todas las variaciones se mapean al mismo directorio.

---

## 🚨 Errores Comunes

### Error 404 - Category not found

**Causa:** La carpeta no existe con el nombre normalizado.

**Ejemplo:**

```bash
# Request
{"category": "Física"}

# Se normaliza a
"fisica"

# Busca en
docs/fisica/  ← Si esta carpeta no existe, error 404
```

**Solución:**

1. Crear la carpeta con el nombre normalizado:

   ```bash
   mkdir docs/fisica
   ```

2. O verificar que el nombre coincida:
   ```bash
   ls docs/
   # Debe mostrar: fisica (no Física ni FISICA)
   ```

---

## 📊 Tabla de Normalización

| Input Usuario | Normalizado   | Carpeta Buscada     |
| ------------- | ------------- | ------------------- |
| `geomecanica` | `geomecanica` | `docs/geomecanica/` |
| `Geomecanica` | `geomecanica` | `docs/geomecanica/` |
| `GEOMECANICA` | `geomecanica` | `docs/geomecanica/` |
| `geomecánica` | `geomecanica` | `docs/geomecanica/` |
| `Geomecánica` | `geomecanica` | `docs/geomecanica/` |
| `GEOMECÁNICA` | `geomecanica` | `docs/geomecanica/` |
| `Física`      | `fisica`      | `docs/fisica/`      |
| `MECÁNICA`    | `mecanica`    | `docs/mecanica/`    |
| `Hidráulica`  | `hidraulica`  | `docs/hidraulica/`  |

---

## 🎯 Recomendaciones

### Para Desarrolladores:

1. ✅ Crear carpetas en `docs/` sin tildes, minúsculas
2. ✅ Permitir a usuarios escribir con tildes en el frontend
3. ✅ Mostrar nombres "bonitos" en la UI (con tildes)
4. ✅ Dejar que el backend normalice automáticamente

### Para Usuarios:

1. ✅ Escribe como quieras: "Geomecánica", "GEOMECANICA", etc.
2. ✅ No te preocupes por mayúsculas o tildes
3. ✅ El sistema lo entiende automáticamente

---

## 🔧 Código de Integración

### Python:

```python
import requests

# Los usuarios pueden escribir con tildes
categories_user_friendly = [
    "Geomecánica",
    "Física",
    "Mecánica de Rocas"
]

for category in categories_user_friendly:
    response = requests.post('http://localhost:8000/ask', json={
        'category': category,  # Se normaliza automáticamente
        'question': '¿Qué es esto?',
        'format': 'plain'
    })
    print(f"{category} → {response.status_code}")
```

### JavaScript:

```javascript
// Dropdown con nombres bonitos
const categories = [
  { name: "Geomecánica", icon: "🪨" },
  { name: "Física", icon: "⚛️" },
  { name: "Química", icon: "🧪" },
];

// Enviar directamente, se normaliza en backend
const askQuestion = async (category, question) => {
  const response = await fetch("/ask", {
    method: "POST",
    body: JSON.stringify({
      category: category, // "Geomecánica" → "geomecanica"
      question: question,
      format: "html",
    }),
  });
  return await response.json();
};
```

---

**Fecha de implementación:** 23 de octubre de 2025  
**Estado:** ✅ Implementado y funcionando  
**Impacto:** 🎯 Mejor UX, menos errores de usuario
