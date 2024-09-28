from pydantic import BaseModel
from typing import List
from datetime import datetime

# Definir el esquema para un video individual
class VideoItem(BaseModel):
    id: int
    download: str
    url: str
    channel_name: str
    video_publication_date: datetime
    added_at: datetime

# Definir el modelo que contendrá la lista de videos
class VideoList(BaseModel):
    videos: List[VideoItem]