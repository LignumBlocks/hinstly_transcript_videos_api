from celery import Celery

# Conexión a Redis en localhost (127.0.0.1) en el puerto predeterminado 6379
celery = Celery(
    "tasks",
    #broker="redis://localhost:6379/0", 
    #backend="redis://localhost:6379/0"
    broker="redis://red-crs9955ds78s73e2o5og:6379/0", 
    backend="redis://red-crs9955ds78s73e2o5og:6379/0"
)

# Importa las tareas
from tasks.video_processing import process_video
