import os
import glob
import dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
import hashlib
from typing import Dict
import json
import unicodedata

# Cargar variables de entorno
dotenv.load_dotenv()

# Inicializar FastAPI
app = FastAPI()

# Configurar el modelo optimizado
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=800,
    request_timeout=30
)

# Cache global
vectorstore_cache: Dict[str, Chroma] = {}
answer_cache: Dict[str, dict] = {}
PERSIST_DIRECTORY = "chroma_db"

# Modelos de datos
class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"

class VideoQuestionRequest(BaseModel):
    question: str
    video_id: str
    category: str = "geomecanica"
    format: str = "both"


def normalize_category(category: str) -> str:
    """Normaliza el nombre de la categoría."""
    category = category.lower()
    category = unicodedata.normalize('NFD', category)
    category = ''.join(char for char in category if unicodedata.category(char) != 'Mn')
    return category


def get_cache_key(question: str, category: str, format_type: str) -> str:
    """Genera clave única para caché."""
    content = f"{question.lower().strip()}:{category}:{format_type}"
    return hashlib.md5(content.encode()).hexdigest()


def cache_answer(cache_key: str, answer: dict):
    """Guarda respuesta en caché (máximo 100)."""
    if len(answer_cache) >= 100:
        first_key = next(iter(answer_cache))
        del answer_cache[first_key]
    answer_cache[cache_key] = answer


def get_or_create_vectorstore(category: str):
    """Obtiene el vectorstore para una categoría (usa nombres simples)."""
    category = normalize_category(category)
    
    # Verificar que la categoría existe
    docs_path = f"docs/{category}"
    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")
    
    # Cache en memoria
    if category in vectorstore_cache:
        return vectorstore_cache[category]
    
    # Cargar desde disco usando el nombre de categoría directamente
    embeddings = OpenAIEmbeddings()
    
    try:
        print(f"📦 Cargando vectorstore '{category}' desde disco...")
        vectorstore = Chroma(
            collection_name=category,
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        
        # Verificar que tiene documentos
        test_docs = vectorstore.similarity_search("test", k=1)
        if not test_docs:
            raise HTTPException(
                status_code=500, 
                detail=f"Vectorstore '{category}' existe pero está vacío. Ejecuta: python reindex_documents.py"
            )
        
        vectorstore_cache[category] = vectorstore
        print(f"✅ Vectorstore '{category}' cargado correctamente")
        return vectorstore
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cargando vectorstore '{category}': {str(e)}. Ejecuta: python reindex_documents.py"
        )


def get_video_mapping(category: str = "geomecanica") -> Dict[str, str]:
    """Retorna mapeo de IDs de video a archivos."""
    category = normalize_category(category)
    videos_path = f"videos/{category}"
    
    if not os.path.exists(videos_path):
        return {}
    
    txt_files = glob.glob(os.path.join(videos_path, "*.txt"))
    mapping = {}
    
    for txt_file in txt_files:
        filename = os.path.basename(txt_file)
        if filename.startswith("Modulo_"):
            parts = filename.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                video_id = f"modulo_{parts[1]}"
                mapping[video_id] = txt_file
        else:
            video_id = os.path.splitext(filename)[0].lower().replace(" ", "_")
            mapping[video_id] = txt_file
    
    return mapping


def load_video_transcription(video_id: str, category: str = "geomecanica"):
    """Carga la transcripción de un video."""
    from langchain.schema import Document
    
    category = normalize_category(category)
    video_mapping = get_video_mapping(category)
    
    if video_id.lower() not in video_mapping:
        available_ids = list(video_mapping.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Video ID '{video_id}' not found. Available: {available_ids}"
        )
    
    txt_file = video_mapping[video_id.lower()]
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    document = Document(
        page_content=content,
        metadata={
            "source": txt_file,
            "video_id": video_id,
            "category": category,
            "type": "video_transcription"
        }
    )
    
    return [document]


def get_or_create_video_vectorstore(video_id: str, category: str = "geomecanica"):
    """Crea vectorstore para un video."""
    category = normalize_category(category)
    cache_key = f"video_{category}_{video_id}"
    
    if cache_key in vectorstore_cache:
        return vectorstore_cache[cache_key]
    
    documents = load_video_transcription(video_id, category)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )
    splits = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()
    persist_path = os.path.join(PERSIST_DIRECTORY, f"video_{category}_{video_id}")
    
    if os.path.exists(persist_path):
        vectorstore = Chroma(
            persist_directory=persist_path,
            embedding_function=embeddings
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_path
        )
    
    vectorstore_cache[cache_key] = vectorstore
    return vectorstore


@app.post("/ask")
async def ask_question(question_request: QuestionRequest):
    """
    Endpoint simplificado - Deja que la IA evalúe si hay información relevante.
    Sin validaciones complejas, sin filtros de keywords.
    La IA es lo suficientemente inteligente para manejar esto.
    """
    question = question_request.question
    category = normalize_category(question_request.category)
    format_type = question_request.format.lower()
    
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    try:
        # Verificar caché
        cache_key = get_cache_key(question, category, format_type)
        if cache_key in answer_cache:
            print(f"⚡ Respuesta del caché")
            return answer_cache[cache_key]
        
        # Obtener vectorstore y buscar documentos relevantes
        vectorstore = get_or_create_vectorstore(category)
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 2, "fetch_k": 10}
        )
        
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Extraer fuentes
        sources_info = []
        for doc in relevant_docs:
            fuente = doc.metadata.get("source", "Fuente desconocida")
            pagina = doc.metadata.get("page", "Página no especificada")
            sources_info.append(f"{fuente} (pág. {pagina})")
        
        sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
        sources_plain = "\n".join(f"• {source}" for source in sources_info)
        
        result = {
            "question": question,
            "category": category,
            "format": format_type
        }
        
        # Prompt SIMPLE y DIRECTO - Sin mencionar "contexto"
        if format_type in ["html", "both"]:
            prompt = f"""Basándote en la siguiente información de documentos técnicos, responde de forma directa y concisa:

INFORMACIÓN DISPONIBLE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "el contexto" o "los documentos"
- Sé conciso y específico
- Si la información no está disponible, di: "No tengo información sobre esto en la base de datos."
- Usa formato HTML: <p>, <ul>, <li>, <strong>

Respuesta:"""
            
            result["answer"] = llm.invoke(prompt).content
            result["sources"] = f"<ul>{sources_html}</ul>"
        
        if format_type in ["plain", "both"]:
            prompt = f"""Basándote en la siguiente información de documentos técnicos, responde de forma directa y concisa:

INFORMACIÓN DISPONIBLE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "el contexto" o "los documentos"
- Sé conciso y específico
- Si la información no está disponible, di: "No tengo información sobre esto en la base de datos."
- Usa texto plano

Respuesta:"""
            
            result["answer_plain"] = llm.invoke(prompt).content
            result["sources_plain"] = sources_plain
        
        # Guardar en caché
        cache_answer(cache_key, result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-video")
async def ask_video_question(request: VideoQuestionRequest):
    """Endpoint para videos - También simplificado."""
    question = request.question
    video_id = request.video_id.lower()
    category = normalize_category(request.category)
    format_type = request.format.lower()
    
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    try:
        vectorstore = get_or_create_video_vectorstore(video_id, category)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        video_metadata = relevant_docs[0].metadata if relevant_docs else {}
        video_source = video_metadata.get("source", "Fuente desconocida")
        
        sources_html = f"<li>Video: {video_id} ({video_source})</li>"
        sources_plain = f"• Video: {video_id} ({video_source})"
        
        result = {
            "question": question,
            "video_id": video_id,
            "category": category,
            "format": format_type
        }
        
        if format_type in ["html", "both"]:
            prompt = f"""Basándote en la transcripción del video, responde de forma directa y concisa:

TRANSCRIPCIÓN:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "la transcripción" o "el video"
- Sé conciso y específico
- Si no hay información, di: "No tengo información sobre esto en este video."
- Usa formato HTML: <p>, <ul>, <strong>

Respuesta:"""
            
            answer = llm.invoke(prompt).content
            result["answer_html"] = f"""
<div>
    <h2>Video {video_id.upper()}</h2>
    {answer}
    <hr>
    <h4>📹 Fuente:</h4>
    <ul>{sources_html}</ul>
</div>
"""
        
        if format_type in ["plain", "both"]:
            prompt = f"""Basándote en la transcripción del video, responde de forma directa y concisa:

TRANSCRIPCIÓN:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "la transcripción" o "el video"
- Sé conciso y específico
- Si no hay información, di: "No tengo información sobre esto en este video."
- Usa texto plano

Respuesta:"""
            
            answer = llm.invoke(prompt).content
            result["answer_plain"] = f"{answer}"
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{category}")
async def list_videos(category: str):
    """Lista videos disponibles."""
    try:
        category = normalize_category(category)
        video_mapping = get_video_mapping(category)
        
        if not video_mapping:
            raise HTTPException(status_code=404, detail=f"No videos in '{category}'")
        
        videos_info = {}
        for video_id, filepath in video_mapping.items():
            videos_info[video_id] = {
                "filename": os.path.basename(filepath),
                "path": filepath
            }
        
        return {
            "category": category,
            "total_videos": len(videos_info),
            "videos": videos_info
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def cache_stats():
    """Estadísticas del caché."""
    return {
        "answer_cache_size": len(answer_cache),
        "answer_cache_max": 100,
        "vectorstore_cache_size": len(vectorstore_cache)
    }


@app.delete("/cache/clear")
async def clear_cache():
    """Limpia el caché."""
    cleared = len(answer_cache)
    answer_cache.clear()
    return {"message": f"Caché limpiado: {cleared} items"}


@app.get("/categories")
async def list_categories():
    """Lista categorías disponibles."""
    docs_path = "docs"
    if not os.path.exists(docs_path):
        return {"categories": []}
    
    categories = [
        d for d in os.listdir(docs_path) 
        if os.path.isdir(os.path.join(docs_path, d)) and not d.startswith('.')
    ]
    
    return {"categories": categories}


@app.get("/")
async def root():
    """Info de la API."""
    return {
        "message": "PDF & Video RAG API - ⚡ OPTIMIZADA Y DIRECTA",
        "version": "3.0 - AI-Powered Simple",
        "philosophy": "Respuestas directas y concisas. La IA evalúa relevancia sin mencionar 'contexto'.",
        "optimizations": [
            "✅ gpt-4o-mini: 15-20x más rápido",
            "✅ Caché de respuestas: <50ms para repetidas",
            "✅ MMR search: Mejor relevancia (k=2)",
            "✅ Prompts directos: Sin mencionar 'contexto'",
            "✅ Respuestas concisas: Información específica"
        ],
        "endpoints": {
            "/ask": "POST - Consulta PDFs por categoría",
            "/ask-video": "POST - Consulta videos por ID",
            "/videos/{category}": "GET - Lista videos disponibles",
            "/categories": "GET - Lista categorías de PDFs",
            "/cache/stats": "GET - Estadísticas del caché",
            "/cache/clear": "DELETE - Limpia caché de respuestas"
        },
        "note": "Los documentos deben estar indexados. Ejecuta: python reindex_documents.py"
    }


@app.on_event("shutdown")
def cleanup():
    """Limpieza al cerrar."""
    vectorstore_cache.clear()
    answer_cache.clear()
