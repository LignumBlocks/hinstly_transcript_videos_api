import os
import psycopg2
from celery_app import celery
from dotenv import load_dotenv
from vosk import Model
import requests
import zipfile
from services.storage_provider_transcriptions import PostgresTranscriptionProvider  # Importar el almacenamiento en PostgreSQL
from datetime import datetime
import psycopg2
import subprocess

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Asegúrate de que el modelo Vosk esté disponible
model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
model_dir = "/mnt/data/vosk_model"

def ensure_vosk_model():
    if not os.path.exists(model_dir):
        print("no existia el directorio /mnt/data/vosk_model")
        os.makedirs(model_dir)
        # Descargar y descomprimir el modelo
        print(f"descargando el modelo")
        response = requests.get(model_url, stream=True)
        with open("/mnt/data/vosk_model.zip", "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        with zipfile.ZipFile("/mnt/data/vosk_model.zip", 'r') as zip_ref:
            zip_ref.extractall(model_dir)
    print("Modelo de Vosk disponible.")

# Cargar el modelo de Vosk
ensure_vosk_model()
model = Model(model_dir)

# Inicializar el proveedor de almacenamiento para transcripciones
transcription_provider = PostgresTranscriptionProvider()

@celery.task(bind=True)
def process_video(self, video_data):
    task_id = self.request.id
    download_url = video_data["download"]
    video_url = video_data["url"]
    channel_name = video_data["channel_name"]
    video_publication_date = video_data["video_publication_date"]

    video_output_path = f"static/{task_id}_video.mp4"
    audio_output_path = f"static/{task_id}_audio.wav"
    transcription_output_path = f"static/{task_id}_transcription.txt"

    try:
        # 1. Descargar el video
        video_path = download_video(download_url, video_output_path)
        if not video_path:
            return f"Error al descargar el video: {download_url}"

        # 2. Extraer el audio del video
        audio_path = extract_audio(video_path, audio_output_path)
        if not audio_path:
            return f"Error al extraer el audio del video: {download_url}"

        # 3. Transcribir el audio usando Vosk
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return f"Error al transcribir el audio del video: {download_url}"

        # 4. Guardar la transcripción en un archivo .txt
        with open(transcription_output_path, "w") as file:
            file.write(transcription)

        # 5. Guardar la transcripción en la base de datos usando el proveedor desacoplado
        transcription_provider.store({
            "transcriptions": [{
                "download": download_url,
                "content": transcription,
                "url": video_url,
                "channel_name": channel_name,
                "video_identifier": task_id,  # Aquí puedes usar el task_id como identificador
                "video_publication_date": video_publication_date,
                "added_at": datetime.now()
            }]
        })

        print(f"Transcripción guardada en {transcription_output_path} y en la base de datos.")
        return transcription_output_path

    finally:
        # Limpiar archivos temporales de video y audio
        if os.path.exists(video_output_path):
            os.remove(video_output_path)
        if os.path.exists(audio_output_path):
            os.remove(audio_output_path)


# Función para descargar el video
def download_video(url, output_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el video: {e}")
        return None

# Extraer el audio con ffmpeg
def extract_audio(video_path, audio_output_path):
    try:
        command = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            audio_output_path
        ]
        subprocess.run(command, check=True)
        print(f"Audio extraído en: {audio_output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error al extraer el audio: {e}")
        return None
    return audio_output_path

# Transcribir el audio con Vosk
def transcribe_audio(audio_path):
    model = vosk.Model(model_dir)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with open(audio_path, "rb") as audio_file:
        data = audio_file.read(4000)
        while len(data) > 0:
            recognizer.AcceptWaveform(data)
            data = audio_file.read(4000)
        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "")
