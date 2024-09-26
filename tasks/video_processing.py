import requests
import subprocess
import os
import vosk
import json

# Descargar el video
def download_video(url, output_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Video descargado en: {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el video: {e}")
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

@celery.task
def process_video(url):
    video_output_path = "static/video.mp4"
    audio_output_path = "static/audio.wav"

    video_path = download_video(url, video_output_path)
    if not video_path:
        return f"Error al descargar el video: {url}"

    audio_path = extract_audio(video_path, audio_output_path)
    if not audio_path:
        return f"Error al extraer el audio del video: {url}"

    transcription = transcribe_audio(audio_path)
    if not transcription:
        return f"Error al transcribir el audio del video: {url}"

    print(f"Transcripción del video en {url}: {transcription}")
    return transcription
