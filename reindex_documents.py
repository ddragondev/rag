"""
Script para re-indexar todos los documentos en Chroma con nombres de colección correctos
"""
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
    length_function=len
)

# Directorios de documentos
DOCS_CONFIG = {
    "geomecanica": "docs/geomecanica",
    "compliance": "docs/compliance"
}

def clear_chroma_db():
    """Limpia la base de datos Chroma"""
    if os.path.exists("./chroma_db"):
        print("🗑️  Eliminando base de datos anterior...")
        shutil.rmtree("./chroma_db")
        print("✅ Base de datos eliminada")

def index_category(category: str, docs_path: str):
    """Indexa todos los PDFs de una categoría"""
    print(f"\n📚 Indexando categoría: {category}")
    print(f"📂 Ruta: {docs_path}")
    
    if not os.path.exists(docs_path):
        print(f"⚠️  Directorio no existe: {docs_path}")
        return
    
    # Obtener todos los PDFs
    pdf_files = [f for f in os.listdir(docs_path) if f.endswith('.pdf')]
    print(f"📄 Encontrados {len(pdf_files)} archivos PDF")
    
    all_documents = []
    
    # Procesar cada PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(docs_path, pdf_file)
        print(f"  ⏳ Procesando: {pdf_file}")
        
        try:
            # Cargar PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Dividir en chunks
            chunks = text_splitter.split_documents(documents)
            
            # Agregar metadata
            for chunk in chunks:
                chunk.metadata['category'] = category
                chunk.metadata['source_file'] = pdf_file
            
            all_documents.extend(chunks)
            print(f"    ✅ {len(chunks)} chunks creados")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Crear vectorstore si hay documentos
    if all_documents:
        print(f"\n💾 Creando vectorstore para '{category}'...")
        print(f"📊 Total de chunks: {len(all_documents)}")
        
        # Procesar en lotes de 100 documentos para evitar límite de tokens
        BATCH_SIZE = 100
        vectorstore = None
        
        for i in range(0, len(all_documents), BATCH_SIZE):
            batch = all_documents[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(all_documents) + BATCH_SIZE - 1) // BATCH_SIZE
            
            print(f"  📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            if vectorstore is None:
                # Crear el vectorstore con el primer lote
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    collection_name=category,
                    persist_directory="./chroma_db"
                )
            else:
                # Agregar documentos al vectorstore existente
                vectorstore.add_documents(batch)
            
            print(f"    ✅ Lote {batch_num} procesado")
        
        print(f"✅ Vectorstore '{category}' creado exitosamente")
        
        # Verificar
        test_results = vectorstore.similarity_search("test", k=1)
        print(f"✅ Verificación: {len(test_results)} documentos accesibles")
    else:
        print(f"⚠️  No se encontraron documentos para indexar en {category}")

def main():
    print("=" * 60)
    print("🚀 RE-INDEXACIÓN DE DOCUMENTOS")
    print("=" * 60)
    
    # Limpiar base de datos anterior
    clear_chroma_db()
    
    # Indexar cada categoría
    for category, docs_path in DOCS_CONFIG.items():
        index_category(category, docs_path)
    
    print("\n" + "=" * 60)
    print("✅ RE-INDEXACIÓN COMPLETADA")
    print("=" * 60)
    
    # Resumen final
    print("\n📊 RESUMEN:")
    for category in DOCS_CONFIG.keys():
        try:
            db = Chroma(
                collection_name=category,
                embedding_function=embeddings,
                persist_directory="./chroma_db"
            )
            # Contar documentos (aproximado)
            test = db.similarity_search("test", k=100)
            print(f"  • {category}: ~{len(test)}+ documentos")
        except Exception as e:
            print(f"  • {category}: Error - {e}")

if __name__ == "__main__":
    main()
