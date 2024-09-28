from abc import ABC, abstractmethod
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from dotenv import load_dotenv
import os

# Cargar las variables de entorno
load_dotenv()

# Configurar SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` para ver las consultas SQL generadas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir el modelo de la tabla transcriptions
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    download = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(255), nullable=False)
    channel_name = Column(String(255), nullable=True)
    video_publication_date = Column(Date, nullable=True)
    added_at = Column(DateTime, default=datetime.now)

# Definir la interfaz abstracta para los proveedores de almacenamiento
class StorageProvider(ABC):
    @abstractmethod
    def store(self, data: dict):
        pass

# Implementación que almacena los datos en la tabla transcriptions en PostgreSQL
class PostgresTranscriptionProvider(StorageProvider):
    def __init__(self):
        self.db = SessionLocal()

    def store(self, data: dict):
        try:
            for transcription_data in data["transcriptions"]:
                # Insertar la transcripción en la base de datos
                transcription_entry = Transcription(
                    download=transcription_data["download"],
                    content=transcription_data["content"],
                    url=transcription_data["url"],
                    channel_name=transcription_data.get("channel_name", None),
                    video_publication_date=transcription_data.get("video_publication_date", None),
                    added_at=transcription_data.get("added_at", datetime.now())  # Usar la fecha actual si no se proporciona
                )
                self.db.add(transcription_entry)

            # Confirmamos los cambios en la base de datos
            self.db.commit()
            print("Transcripciones almacenadas en la base de datos.")
        except IntegrityError:
            self.db.rollback()  # Deshacer los cambios si hay errores
            print(f"Error de integridad, posiblemente un duplicado.")
        except Exception as e:
            self.db.rollback()  # Deshacer los cambios en caso de otros errores
            print(f"Error al almacenar las transcripciones: {str(e)}")
        finally:
            self.db.close()  # Cerrar la sesión
