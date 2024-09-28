from fastapi import FastAPI
from models.video_urls import VideoList
from celery_app import process_video

app = FastAPI()

@app.post("/transcribe-videos")
async def transcribe_videos(video_list: VideoList):
    for video in video_list.videos:
        # Pasar el video como un diccionario a la tarea de Celery
        process_video.delay(video.dict())
    return {"message": "Videos en proceso", "videos": video_list.videos}
