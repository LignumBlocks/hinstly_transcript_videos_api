from pydantic import BaseModel, RootModel

# Definir el esquema para un video individual
class VideoItem(BaseModel):
    id: int
    origin: str
    download: str
    processed: bool
    source: str

# Definir el modelo que contendrá la lista de videos
class VideoList(RootModel[list[VideoItem]]):
    pass