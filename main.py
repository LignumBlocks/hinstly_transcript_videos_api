from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/transcribe-videos")
async def transcribe_videos(urls: list[str]):
    # Aquí más adelante se colocará la lógica de encolar las tareas
    return {"message": "Received URLs", "urls": urls}

#end