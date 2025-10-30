"""
Procesador de videos MP4 para RAG
Extrae audio, transcribe con Whisper y opcionalmente analiza frames
"""
import os
import subprocess
from pathlib import Path
from typing import List, Optional
import json
from langchain.schema import Document
from openai import OpenAI
import tempfile

class MP4Processor:
    """Procesa videos MP4 para extraer contenido textual."""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extrae el audio de un video MP4.
        
        Args:
            video_path: Ruta al archivo MP4
            output_path: Ruta de salida para el audio (opcional)
            
        Returns:
            Ruta al archivo de audio extraído
        """
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            video_name = Path(video_path).stem
            output_path = os.path.join(temp_dir, f"{video_name}_audio.mp3")
        
        # Usar ffmpeg para extraer audio
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',  # Codec de audio
            '-ab', '192k',  # Bitrate
            '-ar', '44100',  # Sample rate
            '-y',  # Sobrescribir si existe
            output_path
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"✅ Audio extraído: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error al extraer audio: {e.stderr.decode()}")
        except FileNotFoundError:
            raise Exception("ffmpeg no está instalado. Instala con: brew install ffmpeg")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe un archivo de audio usando Whisper de OpenAI.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Transcripción del audio
        """
        print(f"🎤 Transcribiendo audio con Whisper...")
        
        # Verificar tamaño del archivo (límite de 25MB para Whisper API)
        file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
        
        if file_size > 25:
            print(f"⚠️  Archivo grande ({file_size:.1f}MB), considera dividirlo")
        
        with open(audio_path, 'rb') as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        print(f"✅ Transcripción completada ({len(transcript.text)} caracteres)")
        return transcript.text
    
    def extract_frames(
        self, 
        video_path: str, 
        output_dir: str,
        fps: float = 0.1  # 1 frame cada 10 segundos por defecto
    ) -> List[str]:
        """
        Extrae frames del video a intervalos regulares.
        
        Args:
            video_path: Ruta al video MP4
            output_dir: Directorio para guardar los frames
            fps: Frames por segundo a extraer (default: 0.1 = 1 cada 10s)
            
        Returns:
            Lista de rutas a los frames extraídos
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps={fps}',
            '-q:v', '2',  # Calidad
            '-y',
            output_pattern
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            frames = sorted([
                os.path.join(output_dir, f) 
                for f in os.listdir(output_dir) 
                if f.startswith('frame_') and f.endswith('.jpg')
            ])
            print(f"✅ Extraídos {len(frames)} frames")
            return frames
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error al extraer frames: {e.stderr.decode()}")
    
    def process_video(
        self, 
        video_path: str,
        extract_visual: bool = False,
        fps: float = 0.1
    ) -> List[Document]:
        """
        Procesa un video completo: extrae audio, transcribe y opcionalmente analiza frames.
        
        Args:
            video_path: Ruta al video MP4
            extract_visual: Si se deben extraer y analizar frames
            fps: Frames por segundo a extraer si extract_visual=True
            
        Returns:
            Lista de documentos LangChain con el contenido extraído
        """
        video_name = Path(video_path).stem
        documents = []
        
        # 1. Extraer y transcribir audio
        print(f"\n📹 Procesando video: {video_name}")
        print("="*70)
        
        audio_path = self.extract_audio(video_path)
        transcription = self.transcribe_audio(audio_path)
        
        # Crear documento con la transcripción
        doc = Document(
            page_content=transcription,
            metadata={
                "source": video_path,
                "type": "video_transcription",
                "video_name": video_name,
                "duration": self._get_video_duration(video_path)
            }
        )
        documents.append(doc)
        
        # 2. Opcionalmente extraer y analizar frames
        if extract_visual:
            print(f"\n🎬 Extrayendo frames visuales...")
            temp_frames_dir = tempfile.mkdtemp()
            frames = self.extract_frames(video_path, temp_frames_dir, fps)
            
            # Aquí podrías agregar análisis con GPT-4 Vision
            # Por ahora solo guardamos referencia a los frames
            frame_doc = Document(
                page_content=f"Video contiene {len(frames)} frames extraídos",
                metadata={
                    "source": video_path,
                    "type": "video_frames",
                    "video_name": video_name,
                    "frames_count": len(frames),
                    "frames_dir": temp_frames_dir
                }
            )
            documents.append(frame_doc)
        
        # Limpiar archivo de audio temporal
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        print(f"\n✅ Video procesado: {len(documents)} documentos creados")
        print("="*70)
        
        return documents
    
    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """Obtiene la duración del video en segundos."""
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            return None


# Función de utilidad para cargar todos los MP4 de una carpeta
def load_mp4_documents(
    directory: str,
    openai_api_key: str,
    extract_visual: bool = False
) -> List[Document]:
    """
    Carga y procesa todos los videos MP4 de un directorio.
    
    Args:
        directory: Ruta al directorio con videos MP4
        openai_api_key: API key de OpenAI
        extract_visual: Si se deben extraer frames visuales
        
    Returns:
        Lista de documentos procesados
    """
    processor = MP4Processor(openai_api_key)
    all_documents = []
    
    mp4_files = [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.lower().endswith('.mp4')
    ]
    
    if not mp4_files:
        print(f"⚠️  No se encontraron archivos MP4 en {directory}")
        return []
    
    print(f"\n📂 Encontrados {len(mp4_files)} videos MP4")
    
    for video_path in mp4_files:
        try:
            docs = processor.process_video(video_path, extract_visual)
            all_documents.extend(docs)
        except Exception as e:
            print(f"❌ Error procesando {video_path}: {e}")
    
    return all_documents


# Ejemplo de uso
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Procesar un solo video
    processor = MP4Processor(api_key)
    
    # Ejemplo 1: Solo transcripción de audio
    docs = processor.process_video("docs/videos/mi_video.mp4")
    
    # Ejemplo 2: Con análisis visual
    docs = processor.process_video(
        "docs/videos/mi_video.mp4",
        extract_visual=True,
        fps=0.1  # 1 frame cada 10 segundos
    )
    
    # Ejemplo 3: Cargar todos los MP4 de una carpeta
    all_docs = load_mp4_documents(
        "docs/videos",
        api_key,
        extract_visual=False
    )
    
    print(f"\n📊 Total de documentos: {len(all_docs)}")
    for doc in all_docs:
        print(f"  - {doc.metadata['type']}: {doc.metadata['video_name']}")
