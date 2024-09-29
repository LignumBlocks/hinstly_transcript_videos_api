from abc import ABC, abstractmethod
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError  # Importar la excepción para manejar duplicados
from dotenv import load_dotenv
import os
from datetime import datetime

# Cargar las variables de entorno
load_dotenv()

# Configurar SQLAlchemy
DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` para ver las consultas SQL generadas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir el modelo de la tabla videos_queue
class VideoQueue(Base):
    __tablename__ = "videos_queue"

    id = Column(Integer, primary_key=True, index=True)
    download = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)  # "unique=True" para evitar URLs duplicadas
    channel_name = Column(String(255), nullable=True)
    video_publication_date = Column(Date, nullable=True)
    added_at = Column(DateTime, default=datetime.now)

# Definir la interfaz abstracta para los proveedores de almacenamiento
class StorageProvider(ABC):
    @abstractmethod
    def store(self, data: dict):
        pass

# Implementación que almacena los datos en PostgreSQL
class PostgresStorageProvider(StorageProvider):
    def __init__(self):
        self.db = SessionLocal()

    def store(self, data: dict):
        try:
            for video in data["videos"]:
                # Intentamos insertar el video
                video_entry = VideoQueue(
                    download=video["download_link"],
                    url=video["video_url"],
                    channel_name=video.get("channel_name", None),  # Puede ser None si no está disponible
                    video_publication_date=video.get("video_publication_date", None),  # Convertir a formato datetime si está disponible
                    added_at=video.get("added_at", datetime.now())  # Usar la fecha actual si no se proporciona
                )
                self.db.add(video_entry)

            # Intentamos confirmar los cambios
            self.db.commit()  # Confirmamos los cambios en la base de datos
            print("Datos almacenados en la base de datos.")
        except IntegrityError:
            self.db.rollback()  # Deshacer los cambios si hay duplicados
            print(f"El video con la URL {video['video_url']} ya existe en la base de datos.")
        except Exception as e:
            self.db.rollback()  # Deshacer los cambios en caso de otros errores
            print(f"Error al almacenar los datos: {str(e)}")
        finally:
            self.db.close()  # Cerramos la sesión
