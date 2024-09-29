from pydantic import BaseModel

class TikTokRequest(BaseModel):
    profile: str
    videos_count: int
    videoKvStoreIdOrName: str