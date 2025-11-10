"""
Script de migración de configuración JSON a MongoDB
Ejecuta este script una vez para migrar categories_config.json a MongoDB
"""

import json
import os
import dotenv
from mongo_manager import MongoManager
from datetime import datetime

# Cargar variables de entorno desde .env
dotenv.load_dotenv()


def migrate_categories_config():
    """Migra categories_config.json a MongoDB."""
    
    config_file = "categories_config.json"
    
    # Verificar que el archivo existe
    if not os.path.exists(config_file):
        print(f"⚠️ Archivo {config_file} no encontrado")
        print("💡 Se creará una configuración inicial en MongoDB")
        return create_initial_config()
    
    try:
        # Leer configuración actual
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📖 Leyendo configuración desde {config_file}")
        print(f"📊 Categorías encontradas: {len(config)}")
        
        # Conectar a MongoDB
        mongo = MongoManager()
        
        # Limpiar categorías existentes (para re-migraciones limpias)
        existing_count = mongo.categories_collection.count_documents({})
        if existing_count > 0:
            print(f"🗑️ Limpiando {existing_count} categorías existentes...")
            mongo.categories_collection.delete_many({})
        
        # Migrar cada categoría
        migrated = 0
        for name, cat_config in config.items():
            try:
                mongo.save_category_config(name, cat_config)
                migrated += 1
                print(f"✅ Categoría '{name}' migrada")
            except Exception as e:
                print(f"❌ Error al migrar categoría '{name}': {e}")
        
        print(f"\n🎉 Migración completada: {migrated}/{len(config)} categorías migradas")
        
        # Verificar migración ANTES de hacer backup
        verification_success = verify_migration(mongo, config)
        
        if verification_success:
            # Crear backup del archivo JSON solo si la verificación fue exitosa
            backup_file = f"{config_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Si ya existe un backup, no renombrar, solo copiar
            backup_files = [f for f in os.listdir('.') if f.startswith(config_file + '.backup_')]
            if backup_files:
                print(f"ℹ️ Ya existe un backup previo: {backup_files[0]}")
                print(f"💡 No se creará nuevo backup para evitar perder el archivo original")
            else:
                os.rename(config_file, backup_file)
                print(f"💾 Backup creado: {backup_file}")
        else:
            print(f"⚠️ Verificación falló, no se creará backup")
        
        mongo.close()
        
        return verification_success
    
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False


def create_initial_config():
    """Crea una configuración inicial en MongoDB si no existe JSON."""
    
    try:
        mongo = MongoManager()
        
        # Configuración inicial para categorías comunes
        initial_categories = {
            "geomecanica": {
                "display_name": "Geomecánica",
                "description": "Documentos relacionados con mecánica de rocas, estabilidad de taludes, fortificación y análisis estructural",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "compliance": {
                "display_name": "Cumplimiento",
                "description": "Documentos de normativas, compliance, prevención de delitos y buenas prácticas corporativas",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
        for name, config in initial_categories.items():
            mongo.save_category_config(name, config)
            print(f"✅ Categoría inicial '{name}' creada")
        
        print(f"\n🎉 Configuración inicial creada en MongoDB")
        
        mongo.close()
        
        return True
    
    except Exception as e:
        print(f"❌ Error al crear configuración inicial: {e}")
        return False


def verify_migration(mongo: MongoManager, original_config: dict):
    """Verifica que la migración fue exitosa."""
    
    print("\n🔍 Verificando migración...")
    
    # Cargar categorías desde MongoDB
    mongo_config = mongo.load_categories_config()
    
    # Comparar
    missing = []
    for name in original_config.keys():
        if name not in mongo_config:
            missing.append(name)
    
    if missing:
        print(f"⚠️ Categorías no migradas: {', '.join(missing)}")
        return False
    else:
        print(f"✅ Verificación exitosa: todas las categorías están en MongoDB")
        return True


def show_mongodb_categories():
    """Muestra las categorías almacenadas en MongoDB."""
    
    try:
        mongo = MongoManager()
        
        config = mongo.load_categories_config()
        
        print("\n📋 Categorías en MongoDB:")
        print("=" * 60)
        
        for name, cat in config.items():
            print(f"\n📁 {name}")
            print(f"   Nombre: {cat.get('display_name', 'N/A')}")
            print(f"   Descripción: {cat.get('description', 'N/A')[:80]}...")
            print(f"   Creada: {cat.get('created_at', 'N/A')}")
            print(f"   Actualizada: {cat.get('updated_at', 'N/A')}")
            if cat.get('prompt_html'):
                print(f"   ✓ Tiene prompt HTML personalizado")
            if cat.get('prompt_plain'):
                print(f"   ✓ Tiene prompt Plain personalizado")
        
        print("\n" + "=" * 60)
        print(f"Total: {len(config)} categorías")
        
        mongo.close()
        
    except Exception as e:
        print(f"❌ Error al mostrar categorías: {e}")


if __name__ == "__main__":
    print("🚀 Iniciando migración a MongoDB")
    print("=" * 60)
    
    # Ejecutar migración
    success = migrate_categories_config()
    
    if success:
        print("\n✅ Migración completada exitosamente")
        
        # Mostrar categorías migradas
        show_mongodb_categories()
        
        print("\n💡 Ahora puedes:")
        print("   1. Reiniciar el servidor: el sistema usará MongoDB automáticamente")
        print("   2. El archivo JSON original está respaldado")
        print("   3. Usar los nuevos endpoints de gestión de caché y categorías")
    else:
        print("\n❌ La migración falló. Revisa los errores arriba.")
    
    print("\n" + "=" * 60)
