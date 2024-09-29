from celery import Celery
from dotenv import load_dotenv
import os
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# Conexión a Redis en localhost (127.0.0.1) en el puerto predeterminado 6379
celery = Celery(
    "tasks",
    #broker="redis://localhost:6379/0", 
    #backend="redis://localhost:6379/0"
    broker=REDIS_URL, 
    backend=REDIS_URL
)

# Importa las tareas
from tasks.video_processing import process_video
