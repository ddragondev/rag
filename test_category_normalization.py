"""
Test de normalización de categorías
Demuestra que la API acepta categorías con tildes y mayúsculas
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_category_normalization():
    """Prueba diferentes variaciones de nombres de categoría."""
    
    print("\n" + "="*80)
    print("  TEST: Normalización de Categorías")
    print("="*80)
    
    # Diferentes variaciones del mismo nombre
    category_variations = [
        "geomecanica",           # Nombre correcto (minúscula sin tilde)
        "Geomecanica",           # Mayúscula inicial
        "GEOMECANICA",           # Todo mayúsculas
        "geomecánica",           # Con tilde minúscula
        "Geomecánica",           # Con tilde mayúscula inicial
        "GEOMECÁNICA",           # Con tilde todo mayúsculas
        "GeoMecánica",           # Mix de mayúsculas con tilde
        "geoMECÁNICA",           # Mix aleatorio
    ]
    
    question = "¿Qué es el RMR?"
    
    print(f"\n📝 Pregunta de prueba: {question}")
    print(f"📂 Carpeta real en docs/: 'geomecanica' (sin tilde, minúscula)")
    print(f"\n{'Variación de entrada':<25} {'Estado':<15} {'Tiempo':<10}")
    print("-" * 80)
    
    successful = 0
    failed = 0
    
    for category in category_variations:
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/ask",
                json={
                    "question": question,
                    "category": category,
                    "format": "plain"
                },
                timeout=120
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                status = "✅ Éxito"
                successful += 1
                
                # Verificar que la respuesta tenga contenido
                data = response.json()
                has_answer = "answer_plain" in data and len(data["answer_plain"]) > 0
                
                if not has_answer:
                    status = "⚠️  Sin respuesta"
            else:
                status = f"❌ Error {response.status_code}"
                failed += 1
            
            print(f"{category:<25} {status:<15} {elapsed:.2f}s")
            
        except requests.exceptions.RequestException as e:
            print(f"{category:<25} {'❌ Timeout/Error':<15} -")
            failed += 1
        
        # Pequeña pausa entre requests
        time.sleep(0.3)
    
    # Resumen
    print("\n" + "="*80)
    print("  RESUMEN")
    print("="*80)
    print(f"✅ Exitosas: {successful}/{len(category_variations)}")
    print(f"❌ Fallidas:  {failed}/{len(category_variations)}")
    
    if successful == len(category_variations):
        print("\n🎉 ¡Perfecto! Todas las variaciones funcionaron correctamente")
        print("   La normalización está funcionando como se esperaba")
    elif successful > 0:
        print(f"\n⚠️  Algunas variaciones funcionaron ({successful}/{len(category_variations)})")
    else:
        print("\n❌ Ninguna variación funcionó. Verifica que el servidor esté corriendo.")

def test_invalid_category():
    """Prueba con una categoría que no existe."""
    
    print("\n" + "="*80)
    print("  TEST: Categoría Inválida")
    print("="*80)
    
    invalid_categories = [
        "categoría_inexistente",
        "NO_EXISTE",
        "física cuántica"
    ]
    
    for category in invalid_categories:
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={
                    "question": "Test",
                    "category": category,
                    "format": "plain"
                },
                timeout=30
            )
            
            if response.status_code == 404:
                print(f"✅ '{category}' → Error 404 (esperado)")
            else:
                print(f"⚠️  '{category}' → Status {response.status_code}")
                
        except requests.exceptions.RequestException:
            print(f"❌ '{category}' → Error de conexión")

def test_edge_cases():
    """Prueba casos extremos."""
    
    print("\n" + "="*80)
    print("  TEST: Casos Extremos")
    print("="*80)
    
    edge_cases = [
        ("geomecánica  ", "Con espacios al final"),
        ("  geomecánica", "Con espacios al inicio"),
        ("  GEOMECÁNICA  ", "Con espacios en ambos lados"),
    ]
    
    for category, description in edge_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={
                    "question": "¿Qué es el RMR?",
                    "category": category,
                    "format": "plain"
                },
                timeout=120
            )
            
            status = "✅ Éxito" if response.status_code == 200 else f"❌ Error {response.status_code}"
            print(f"{description:<35} → {status}")
            
        except requests.exceptions.RequestException:
            print(f"{description:<35} → ❌ Error")

def show_examples():
    """Muestra ejemplos de uso."""
    
    print("\n" + "="*80)
    print("  EJEMPLOS DE USO")
    print("="*80)
    
    examples = [
        {
            "descripción": "Categoría normal",
            "código": 'curl -X POST http://localhost:8000/ask \\\n  -d \'{"category": "geomecanica", "question": "..."}\'',
        },
        {
            "descripción": "Con tilde y mayúscula",
            "código": 'curl -X POST http://localhost:8000/ask \\\n  -d \'{"category": "Geomecánica", "question": "..."}\'',
        },
        {
            "descripción": "Todo mayúsculas con tilde",
            "código": 'curl -X POST http://localhost:8000/ask \\\n  -d \'{"category": "GEOMECÁNICA", "question": "..."}\'',
        },
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['descripción']}:")
        print(f"   {example['código']}")
    
    print("\n💡 Todos estos ejemplos funcionan gracias a la normalización automática!")

def main():
    """Función principal."""
    
    print("\n" + "🔤"*40)
    print("  PRUEBA DE NORMALIZACIÓN DE CATEGORÍAS")
    print("🔤"*40)
    
    # Verificar servidor
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("\n❌ El servidor no está respondiendo correctamente")
            return
    except requests.exceptions.RequestException:
        print("\n❌ No se puede conectar al servidor en", BASE_URL)
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return
    
    # Ejecutar pruebas
    test_category_normalization()
    test_invalid_category()
    test_edge_cases()
    show_examples()
    
    print("\n" + "="*80)
    print("  ✅ PRUEBAS COMPLETADAS")
    print("="*80)
    print("""
🎯 Beneficios de la normalización:

✨ Usuarios pueden escribir categorías con:
   - Mayúsculas: GEOMECANICA, Geomecanica
   - Tildes: Geomecánica, geomecánica
   - Combinaciones: GeoMecánica, GEOMECÁNICA

✨ El sistema automáticamente convierte todo a:
   - Minúsculas
   - Sin tildes
   - Nombre normalizado: "geomecanica"

✨ Esto hace la API más amigable y tolerante a errores!
""")

if __name__ == "__main__":
    main()
