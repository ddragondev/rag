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

# Configurar el modelo optimizado para velocidad y costo
# gpt-4o-mini: 15-20x más rápido y 60x más barato que gpt-4
# temperature=0: Respuestas determinísticas y más rápidas
# max_tokens=800: Limitar longitud para mayor velocidad
# streaming=True: Respuestas progresivas (habilitado en endpoints stream)
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Modelo más rápido: ~2-3s vs ~8-12s de gpt-4
    temperature=0,  # Respuestas determinísticas = más rápidas
    max_tokens=800,  # Limitar longitud para velocidad
    request_timeout=30  # Timeout de 30s
)

# Modelo alternativo para consultas simples (aún más rápido)
llm_fast = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=500,  # Respuestas más cortas = más rápidas
    request_timeout=20
) 

# Cache global para vectorstores por categoría
vectorstore_cache: Dict[str, Chroma] = {}

# Cache de respuestas para preguntas frecuentes
# Evita llamadas a GPT para preguntas repetidas
answer_cache: Dict[str, dict] = {}

# Directorio para persistencia de vectorstores
PERSIST_DIRECTORY = "chroma_db"

# Definir el esquema para la solicitud
class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"  # "html", "plain", or "both"

class VideoQuestionRequest(BaseModel):
    question: str
    video_id: str  # ID del video (ej: "modulo_1", "modulo_2", etc.)
    category: str = "geomecanica"  # Categoría de videos
    format: str = "both"  # "html", "plain", or "both"


def normalize_category(category: str) -> str:
    """
    Normaliza el nombre de la categoría:
    - Convierte a minúsculas
    - Elimina tildes y acentos
    - Mantiene guiones y guiones bajos
    
    Ejemplos:
    - "Geomecánica" -> "geomecanica"
    - "GEOMECÁNICA" -> "geomecanica"
    - "Mecánica de Rocas" -> "mecanica de rocas"
    """
    # Convertir a minúsculas
    category = category.lower()
    
    # Eliminar tildes usando NFD (Normalization Form Decomposed)
    # Esto separa los caracteres con tildes en carácter base + tilde
    # Luego filtramos solo los caracteres ASCII
    category = unicodedata.normalize('NFD', category)
    category = ''.join(char for char in category if unicodedata.category(char) != 'Mn')
    
    return category


def get_cache_key(question: str, category: str, format_type: str) -> str:
    """
    Genera una clave única para el caché de respuestas.
    Usa MD5 para crear un hash de la pregunta + categoría + formato.
    """
    content = f"{question.lower().strip()}:{category}:{format_type}"
    return hashlib.md5(content.encode()).hexdigest()


def get_cached_answer(question: str, category: str, format_type: str) -> dict | None:
    """
    Busca una respuesta en caché.
    Retorna None si no existe en caché.
    """
    cache_key = get_cache_key(question, category, format_type)
    return answer_cache.get(cache_key)


def cache_answer(question: str, category: str, format_type: str, answer: dict):
    """
    Guarda una respuesta en caché.
    Limita el tamaño del caché a 100 respuestas para evitar uso excesivo de memoria.
    """
    cache_key = get_cache_key(question, category, format_type)
    
    # Limpiar caché si está muy grande (FIFO simple)
    if len(answer_cache) >= 100:
        # Eliminar el primer elemento (más antiguo)
        first_key = next(iter(answer_cache))
        del answer_cache[first_key]
    
    answer_cache[cache_key] = answer


def is_question_relevant_to_category(question: str, category: str) -> tuple[bool, str]:
    """
    Verifica si la pregunta es relevante para la categoría usando keywords.
    
    Returns:
        (is_relevant, message): Tupla con booleano y mensaje opcional
    """
    # Keywords por categoría
    category_keywords = {
        "geomecanica": [
            "roca", "rocas", "macizo", "minería", "mina", "geomecánica", 
            "geotecnia", "suelo", "túnel", "excavación", "fortificación",
            "soportes", "estabilidad", "talud", "esfuerzo", "resistencia",
            "fractura", "falla", "rmr", "gsı", "q-system", "caída",
            "hundimiento", "deformación", "presión", "tensión", "compresión",
            "mineral", "yacimiento", "perforación", "voladura", "banco",
            "relleno", "caserones", "pilares", "chimenea", "galería",
            "perno", "shotcrete", "cimbra", "acuñadura", "buzamiento",
            "discontinuidad", "diaclasa", "estratificación", "litología"
        ],
        "compliance": [
            "cumplimiento", "normativa", "regulación", "legal", "ley",
            "política", "seguridad", "ambiental", "auditoría", "certificación"
        ]
    }
    
    # Obtener keywords de la categoría
    keywords = category_keywords.get(category, [])
    
    # Convertir pregunta a minúsculas
    question_lower = question.lower()
    
    # Lista de temas claramente fuera de contexto
    off_topic_keywords = [
        "filosofía", "religión", "política", "deportes", "cocina",
        "música", "arte", "literatura", "cine", "televisión",
        "moda", "belleza", "animales domésticos", "videojuegos",
        "astronomía", "biología molecular", "química orgánica",
        "programación", "software", "matemáticas puras", "física cuántica"
    ]
    
    # Verificar si es claramente off-topic
    for off_keyword in off_topic_keywords:
        if off_keyword in question_lower:
            return False, f"La pregunta parece ser sobre '{off_keyword}', que no está relacionado con {category}."
    
    # Si la pregunta es muy corta, permitirla (podría ser relevante)
    if len(question.split()) <= 3:
        return True, ""
    
    # Verificar si contiene al menos una keyword relevante
    has_keyword = any(keyword in question_lower for keyword in keywords)
    
    if not has_keyword and len(question.split()) > 5:
        # Pregunta larga sin keywords relevantes - probablemente off-topic
        return False, f"La pregunta no parece estar relacionada con {category}. Por favor, consulta temas sobre geomecánica, minería o ingeniería de rocas."
    
    return True, ""


def get_category_hash(category: str, pdf_files: list) -> str:
    """Genera un hash único basado en la categoría y los archivos PDF."""
    files_str = "".join(sorted(pdf_files))
    content = f"{category}:{files_str}"
    return hashlib.md5(content.encode()).hexdigest()


def get_or_create_vectorstore(category: str):
    """Obtiene el vectorstore del cache o lo crea si no existe."""
    # Normalizar categoría
    category = normalize_category(category)
    
    docs_path = f"docs/{category}"
    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")
    
    # Obtener todos los PDFs de la categoría
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=404, detail=f"No PDF files found in category '{category}'.")
    
    # Generar hash para identificar esta colección
    category_hash = get_category_hash(category, pdf_files)
    persist_path = os.path.join(PERSIST_DIRECTORY, category_hash)
    
    # Verificar si ya existe en cache
    if category in vectorstore_cache:
        return vectorstore_cache[category]
    
    # Verificar si existe en disco
    if os.path.exists(persist_path):
        print(f"📦 Cargando vectorstore desde disco para '{category}'...")
        vectorstore = Chroma(
            persist_directory=persist_path,
            embedding_function=OpenAIEmbeddings()
        )
        vectorstore_cache[category] = vectorstore
        return vectorstore
    
    # Si no existe, crearlo
    print(f"🔨 Creando nuevo vectorstore para '{category}'...")
    documents = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(pdf_file)
        documents.extend(loader.load())
    
    # Optimización: chunk_size más grande, menos chunks = menos embeddings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # Aumentado de 1000
        chunk_overlap=150  # Reducido de 200
    )
    splits = text_splitter.split_documents(documents)
    
    # Crear y persistir vectorstore
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(),
        persist_directory=persist_path
    )
    
    vectorstore_cache[category] = vectorstore
    print(f"✅ Vectorstore creado y guardado en disco")
    return vectorstore


def load_documents_from_category(category: str):
    """Carga y procesa todos los PDFs de la categoría especificada."""
    docs_path = f"docs/{category}"
    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")
    
    # Obtener todos los PDFs de la categoría
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=404, detail=f"No PDF files found in category '{category}'.")
    
    documents = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(pdf_file)
        documents.extend(loader.load())
    
    return documents


# ============================================
# FUNCIONES PARA VIDEOS
# ============================================

def get_video_mapping(category: str = "geomecanica") -> Dict[str, str]:
    """
    Retorna un mapeo de IDs de video a archivos de transcripción.
    
    Ejemplo:
    {
        "modulo_1": "Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt",
        "modulo_2": "Modulo_2_-_Causas_o_factores_de_las_caidas_de_rocas_spa.txt",
        ...
    }
    """
    category = normalize_category(category)
    videos_path = f"videos/{category}"
    
    if not os.path.exists(videos_path):
        return {}
    
    # Obtener todos los archivos TXT
    txt_files = glob.glob(os.path.join(videos_path, "*.txt"))
    
    # Crear mapeo automático basado en nombres de archivo
    mapping = {}
    for txt_file in txt_files:
        filename = os.path.basename(txt_file)
        
        # Extraer ID del nombre del archivo
        # Ejemplo: "Modulo_1_-_Profundicemos..." -> "modulo_1"
        if filename.startswith("Modulo_"):
            # Extraer número del módulo
            parts = filename.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                video_id = f"modulo_{parts[1]}"
                mapping[video_id] = txt_file
        else:
            # Para otros formatos, usar el nombre del archivo sin extensión
            video_id = os.path.splitext(filename)[0].lower().replace(" ", "_")
            mapping[video_id] = txt_file
    
    return mapping


def load_video_transcription(video_id: str, category: str = "geomecanica"):
    """
    Carga la transcripción de un video específico.
    
    Args:
        video_id: ID del video (ej: "modulo_1", "modulo_2")
        category: Categoría de videos (default: "geomecanica")
        
    Returns:
        Lista con un documento LangChain conteniendo la transcripción
    """
    from langchain.schema import Document
    
    category = normalize_category(category)
    video_mapping = get_video_mapping(category)
    
    if video_id.lower() not in video_mapping:
        available_ids = list(video_mapping.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Video ID '{video_id}' not found. Available IDs: {available_ids}"
        )
    
    txt_file = video_mapping[video_id.lower()]
    
    # Leer el contenido del archivo
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear documento con metadata
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
    """
    Crea un vectorstore específico para un video.
    Usa caché para evitar reprocesar el mismo video.
    """
    category = normalize_category(category)
    cache_key = f"video_{category}_{video_id}"
    
    # Verificar cache en memoria
    if cache_key in vectorstore_cache:
        print(f"✅ Usando vectorstore en caché para video {video_id}")
        return vectorstore_cache[cache_key]
    
    # Cargar transcripción del video
    documents = load_video_transcription(video_id, category)
    
    # Dividir en chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )
    splits = text_splitter.split_documents(documents)
    
    print(f"📝 Video {video_id}: {len(splits)} chunks creados")
    
    # Crear vectorstore
    embeddings = OpenAIEmbeddings()
    
    # Verificar si existe en disco
    persist_path = os.path.join(PERSIST_DIRECTORY, f"video_{category}_{video_id}")
    
    if os.path.exists(persist_path):
        print(f"📂 Cargando vectorstore desde disco para video {video_id}")
        vectorstore = Chroma(
            persist_directory=persist_path,
            embedding_function=embeddings
        )
    else:
        print(f"🔨 Creando nuevo vectorstore para video {video_id}")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_path
        )
    
    # Guardar en cache
    vectorstore_cache[cache_key] = vectorstore
    
    return vectorstore


@app.post("/ask")
async def ask_question(question_request: QuestionRequest):
    question = question_request.question
    category = normalize_category(question_request.category)  # Normalizar categoría
    format_type = question_request.format.lower()
    
    # Validar formato
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid format. Must be 'html', 'plain', or 'both'"
        )

    try:
        # �️ VALIDACIÓN 1: Detectar preguntas muy fuera de contexto
        is_relevant, relevance_message = is_question_relevant_to_category(question, category)
        
        if not is_relevant:
            # Pregunta claramente fuera de contexto
            return {
                "question": question,
                "category": category,
                "format": format_type,
                "answer_plain": f"❌ {relevance_message}\n\nPor favor, consulta temas relacionados con geomecánica, minería, mecánica de rocas, fortificación, estabilidad de taludes, etc.",
                "sources_plain": "Sin fuentes (pregunta fuera de contexto)",
                "warning": "off_topic_question"
            }
        
        # �🚀 OPTIMIZACIÓN: Verificar caché primero
        cached_answer = get_cached_answer(question, category, format_type)
        if cached_answer:
            print(f"⚡ Respuesta recuperada del caché (instantánea)")
            return cached_answer
        
        # Usar vectorstore en cache o cargarlo desde disco
        vectorstore = get_or_create_vectorstore(category)
        
        # Configurar retriever optimizado
        # k=2: Solo 2 documentos más relevantes (más rápido, menos tokens)
        # fetch_k=10: Buscar en 10 candidatos antes de filtrar (mejor calidad)
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance: diversidad + relevancia
            search_kwargs={
                "k": 2,  # Reducido a 2 para máxima velocidad
                "fetch_k": 10  # Considerar 10 candidatos
            }
        )

        # Recuperar contexto relevante
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # 🛡️ ANTI-ALUCINACIÓN: Verificar si hay contexto útil
        if not context.strip() or len(context) < 50:
            # No hay suficiente contexto
            return {
                "question": question,
                "category": category,
                "format": format_type,
                "answer_plain": "❌ No encontré información relevante sobre esa pregunta en los documentos de la categoría '{category}'. Por favor, consulta temas relacionados con geomecánica, minería o ingeniería de rocas.",
                "sources_plain": "Sin fuentes relevantes"
            }

        # --- Extraer info de las fuentes --- #
        sources_info = []
        for doc in relevant_docs:
            fuente = doc.metadata.get("source", "Fuente desconocida")
            pagina = doc.metadata.get("page", "Página no especificada")
            sources_info.append(f"{fuente} (pág. {pagina})")

        # Formatear fuentes
        sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
        sources_plain = "\n".join(f"• {source}" for source in sources_info)
        
        # Preparar respuesta base
        result = {
            "question": question,
            "category": category,
            "format": format_type
        }
        
        # Generar respuestas según el formato solicitado
        if format_type in ["html", "both"]:
            # Prompt balanceado: Estricto pero útil
            prompt_html = f"""Basándote ÚNICAMENTE en el siguiente contexto de documentos de geomecánica, responde la pregunta.

CONTEXTO:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde solo con información que aparezca en el contexto
- Si el contexto contiene información relevante, úsala para responder
- Si NO hay información relevante en el contexto, di: "No encontré información específica sobre esto en los documentos."
- Usa formato HTML: <p>, <ul>, <strong>

Respuesta:"""
            
            html_answer = llm.invoke(prompt_html).content
            result["answer"] = html_answer
            result["sources"] = f"<ul>{sources_html}</ul>"
        
        if format_type in ["plain", "both"]:
            # Prompt balanceado: Estricto pero útil
            prompt_plain = f"""Basándote ÚNICAMENTE en el siguiente contexto de documentos de geomecánica, responde la pregunta.

CONTEXTO:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde solo con información que aparezca en el contexto
- Si el contexto contiene información relevante, úsala para responder
- Si NO hay información relevante en el contexto, di: "No encontré información específica sobre esto en los documentos."
- Responde en texto plano

Respuesta:"""
            
            plain_answer = llm.invoke(prompt_plain).content
            result["answer_plain"] = plain_answer
            result["sources_plain"] = sources_plain
        
        # 🚀 OPTIMIZACIÓN: Guardar respuesta en caché
        cache_answer(question, category, format_type, result)
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-stream")
async def ask_question_stream(question_request: QuestionRequest):
    """Endpoint con streaming para respuestas más rápidas y progresivas."""
    question = question_request.question
    category = normalize_category(question_request.category)  # Normalizar categoría
    format_type = question_request.format.lower()
    
    # Validar formato
    if format_type not in ["html", "plain", "both"]:
        async def error_response():
            yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid format. Must be html, plain, or both'})}\n\n"
        return StreamingResponse(error_response(), media_type="text/event-stream")

    async def generate_response():
        try:
            # Usar vectorstore en cache o cargarlo desde disco
            vectorstore = get_or_create_vectorstore(category)
            
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            relevant_docs = retriever.invoke(question)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # Extraer fuentes
            sources_info = []
            for doc in relevant_docs:
                fuente = doc.metadata.get("source", "Fuente desconocida")
                pagina = doc.metadata.get("page", "Página no especificada")
                sources_info.append(f"{fuente} (pág. {pagina})")

            # Formatear fuentes
            sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
            sources_plain = "\n".join(f"• {source}" for source in sources_info)
            
            # Enviar metadata primero
            metadata = {
                "question": question,
                "category": category,
                "format": format_type,
                "type": "metadata"
            }
            
            if format_type in ["html", "both"]:
                metadata["sources"] = f"<ul>{sources_html}</ul>"
            if format_type in ["plain", "both"]:
                metadata["sources_plain"] = sources_plain
                
            yield f"data: {json.dumps(metadata)}\n\n"

            # Stream de la respuesta HTML (si se solicita)
            if format_type in ["html", "both"]:
                prompt_html = (
                    f"Contexto:\n{context}\n\n"
                    f"Pregunta: {question}\n\n"
                    f"Responde en formato HTML con clases de Tailwind (<p>, <strong>, <ul>). "
                    f"Solo proporciona el contenido, sin comentarios adicionales.\n\n"
                )
                
                yield f"data: {json.dumps({{'type': 'html_start'}})}\n\n"
                for chunk in llm.stream(prompt_html):
                    if chunk.content:
                        data = {
                            "type": "html_content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                
                yield f"data: {json.dumps({{'type': 'html_end'}})}\n\n"

            # Stream de la respuesta en texto plano (si se solicita)
            if format_type in ["plain", "both"]:
                prompt_plain = (
                    f"Contexto:\n{context}\n\n"
                    f"Pregunta: {question}\n\n"
                    f"Responde de forma clara y estructurada en texto plano. "
                    f"Solo proporciona el contenido, sin comentarios adicionales.\n\n"
                )
                
                yield f"data: {json.dumps({{'type': 'plain_start'}})}\n\n"
                for chunk in llm.stream(prompt_plain):
                    if chunk.content:
                        data = {
                            "type": "plain_content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data)}\n\n"
            
            # Señal de finalización
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/ask-video")
async def ask_video_question(request: VideoQuestionRequest):
    """
    Endpoint para consultar un video específico por su ID.
    
    Args:
        request: VideoQuestionRequest con question, video_id, category (opcional), format (opcional)
        
    Returns:
        Respuesta basada en la transcripción del video específico
        
    Example:
        POST /ask-video
        {
            "question": "¿Qué es la geomecánica?",
            "video_id": "modulo_1",
            "category": "geomecanica",
            "format": "plain"
        }
    """
    question = request.question
    video_id = request.video_id.lower()
    category = normalize_category(request.category)
    format_type = request.format.lower()
    
    # Validar formato
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid format. Must be 'html', 'plain', or 'both'"
        )

    try:
        # Obtener vectorstore para este video específico
        vectorstore = get_or_create_video_vectorstore(video_id, category)
        
        # Configurar retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        # Recuperar contexto relevante
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # Extraer metadata del video
        video_metadata = relevant_docs[0].metadata if relevant_docs else {}
        video_source = video_metadata.get("source", "Fuente desconocida")
        
        # Información de fuente para este video específico
        sources_html = f"<li>Video: {video_id} ({video_source})</li>"
        sources_plain = f"• Video: {video_id} ({video_source})"

        # Crear respuestas según el formato solicitado
        result = {
            "question": question,
            "video_id": video_id,
            "category": category,
            "format": format_type
        }

        if format_type in ["html", "both"]:
            # Prompt balanceado para video
            prompt_html = f"""Basándote ÚNICAMENTE en la transcripción del video {video_id}, responde la pregunta.

TRANSCRIPCIÓN DEL VIDEO:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde solo con información de la transcripción
- Si la transcripción contiene información relevante, úsala
- Si NO hay información relevante, di: "Este video no cubre ese tema."
- Usa HTML: <p>, <ul>, <strong>

Respuesta:"""
            
            answer_html = llm.invoke(prompt_html).content
            
            result["answer_html"] = f"""
<div>
    <h2>Respuesta del Video {video_id.upper()}</h2>
    {answer_html}
    <hr>
    <h4>📹 Fuente:</h4>
    <ul>{sources_html}</ul>
</div>
"""

        if format_type in ["plain", "both"]:
            # Prompt balanceado para video (texto plano)
            prompt_plain = f"""Basándote ÚNICAMENTE en la transcripción del video {video_id}, responde la pregunta.

TRANSCRIPCIÓN DEL VIDEO:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde solo con información de la transcripción
- Si la transcripción contiene información relevante, úsala
- Si NO hay información relevante, di: "Este video no cubre ese tema."
- Responde en texto plano

Respuesta:"""
            
            answer_plain = llm.invoke(prompt_plain).content
            
            result["answer_plain"] = f"""{answer_plain}

---
📹 Fuente:
{sources_plain}
"""
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{category}")
async def list_videos(category: str):
    """
    Lista todos los videos disponibles en una categoría.
    
    Args:
        category: Categoría de videos (ej: "geomecanica")
        
    Returns:
        Lista de IDs de videos disponibles con sus archivos correspondientes
        
    Example:
        GET /videos/geomecanica
        
        Response:
        {
            "category": "geomecanica",
            "videos": {
                "modulo_1": "Modulo_1_-_Profundicemos_en_las_Generalidades...",
                "modulo_2": "Modulo_2_-_Causas_o_factores_de_las_caidas...",
                ...
            }
        }
    """
    try:
        category = normalize_category(category)
        video_mapping = get_video_mapping(category)
        
        if not video_mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No videos found in category '{category}'"
            )
        
        # Formatear respuesta con nombres más amigables
        videos_info = {}
        for video_id, filepath in video_mapping.items():
            filename = os.path.basename(filepath)
            videos_info[video_id] = {
                "filename": filename,
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


@app.on_event("shutdown")
def cleanup():
    """Eliminar recursos cuando la aplicación se cierra."""
    # No eliminamos las colecciones ya que están persistidas en disco
    vectorstore_cache.clear()
    answer_cache.clear()


@app.get("/cache/stats")
async def cache_stats():
    """
    Retorna estadísticas del caché de respuestas.
    Útil para monitorear el rendimiento.
    """
    return {
        "answer_cache_size": len(answer_cache),
        "answer_cache_max": 100,
        "vectorstore_cache_size": len(vectorstore_cache),
        "info": "El caché de respuestas almacena hasta 100 preguntas frecuentes para respuestas instantáneas"
    }


@app.delete("/cache/clear")
async def clear_cache():
    """
    Limpia el caché de respuestas.
    Útil para forzar regeneración de respuestas.
    """
    cleared_count = len(answer_cache)
    answer_cache.clear()
    return {
        "message": f"Caché limpiado. Se eliminaron {cleared_count} respuestas en caché.",
        "answer_cache_size": 0
    }


@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "PDF & Video RAG API con LangChain - ⚡ OPTIMIZADO",
        "version": "2.0 - High Performance",
        "optimizations": [
            "✅ gpt-4o-mini: 15-20x más rápido que gpt-4",
            "✅ Caché de respuestas: Instantáneo para preguntas repetidas",
            "✅ MMR search: Mejor relevancia con menos documentos",
            "✅ Prompts optimizados: Respuestas más directas",
            "✅ max_tokens limitado: Mayor velocidad"
        ],
        "endpoints": {
            "/ask": "POST - Consulta PDFs por categoría (con caché)",
            "/ask-stream": "POST - Consulta PDFs con streaming",
            "/ask-video": "POST - Consulta un video específico por ID",
            "/videos/{category}": "GET - Lista videos disponibles",
            "/categories": "GET - Lista de categorías de PDFs",
            "/cache/stats": "GET - Estadísticas del caché",
            "/cache/clear": "DELETE - Limpiar caché de respuestas",
            "/docs": "Documentación interactiva Swagger"
        },
        "examples": {
            "ask_pdf": {
                "url": "/ask",
                "method": "POST",
                "body": {
                    "question": "¿Qué es la geomecánica?",
                    "category": "geomecanica",
                    "format": "plain"
                }
            },
            "ask_video": {
                "url": "/ask-video",
                "method": "POST",
                "body": {
                    "question": "¿Qué temas se cubren en este módulo?",
                    "video_id": "modulo_1",
                    "category": "geomecanica",
                    "format": "plain"
                }
            },
            "list_videos": {
                "url": "/videos/geomecanica",
                "method": "GET"
            }
        }
    }


@app.get("/categories")
async def list_categories():
    """Lista todas las categorías de documentos disponibles."""
    docs_path = "docs"
    if not os.path.exists(docs_path):
        return {"categories": []}
    
    categories = [
        d for d in os.listdir(docs_path) 
        if os.path.isdir(os.path.join(docs_path, d)) and not d.startswith('.')
    ]
    
    return {"categories": categories}
