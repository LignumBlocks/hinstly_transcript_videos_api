from celery import Celery

# Conexión a Redis en localhost (127.0.0.1) en el puerto predeterminado 6379
celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",   # Cambia si tienes Redis en otro puerto
    backend="redis://localhost:6379/0"
)

# Importa las tareas
from tasks.video_processing import process_video
