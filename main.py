from fastapi import FastAPI
from models.video_urls import VideoList
from celery_app import process_video

app = FastAPI()

@app.post("/transcribe-videos")
async def transcribe_videos(video_list: VideoList):
    for video in video_list.root:  # Accedemos a la lista de videos usando .root
        process_video.delay(video.dict())  # Pasamos el video a Celery
    return {"message": "Videos en proceso", "videos": video_list.root}
