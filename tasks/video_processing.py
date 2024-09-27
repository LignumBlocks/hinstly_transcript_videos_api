import requests
import subprocess
import os
import vosk
import json
from celery_app import celery
from celery import Task
import psycopg2
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL de conexión a la base de datos desde el archivo .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Descargar el video
def download_video(url, output_path):
    print(f"url------------{url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Video descargado en: {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el video: {url}")
        return None
    return output_path

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
    model_path = "vosk_models/vosk-model-en-us-0.22"
    model = vosk.Model(model_path)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with open(audio_path, "rb") as audio_file:
        data = audio_file.read(4000)
        while len(data) > 0:
            recognizer.AcceptWaveform(data)
            data = audio_file.read(4000)
        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "")

@celery.task(bind=True)
def process_video(self, video_data):
    task_id = self.request.id  # ID único de la tarea
    url = video_data["download"]  # Accedemos a la URL de descarga desde el diccionario
    source = video_data["source"]

    video_output_path = f"static/{task_id}_video.mp4"
    audio_output_path = f"static/{task_id}_audio.wav"
    transcription_output_path = f"static/{task_id}_transcription.txt"

    try:
        # Descargar el video
        video_path = download_video(url, video_output_path)
        if not video_path:
            return f"Error al descargar el video: {url}"

        # Extraer el audio
        audio_path = extract_audio(video_path, audio_output_path)
        if not audio_path:
            return f"Error al extraer el audio del video: {url}"

        # Transcribir el audio
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return f"Error al transcribir el audio del video: {url}"

        # Guardar la transcripción en un archivo .txt
        with open(transcription_output_path, "w") as file:
            file.write(transcription)

        # Guardar la transcripción en la base de datos
        save_transcription_to_db(url, source, transcription)

        print(f"Transcripción guardada en {transcription_output_path} y en la base de datos")
        return transcription_output_path  # Retornamos la ruta del archivo de transcripción

    finally:
        # Limpiar archivos temporales de video y audio
        if os.path.exists(video_output_path):
            os.remove(video_output_path)
        if os.path.exists(audio_output_path):
            os.remove(audio_output_path)


# Guardar la transcripción en la base de datos PostgreSQL
def save_transcription_to_db(download_url, source, transcription):
    try:
        # Conexión a la base de datos usando la URL desde el archivo .env
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO transcriptions (download, source, content)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (download_url, source, transcription))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Transcripción almacenada para el video {download_url}")
    except Exception as e:
        print(f"Error al guardar la transcripción en la base de datos: {e}")
