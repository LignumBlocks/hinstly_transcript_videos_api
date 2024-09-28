from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Definir el modelo de la tabla transcriptions
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    download = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(255), nullable=False)
    channel_name = Column(String(255), nullable=True)
    video_identifier = Column(String(255), nullable=True)
    video_publication_date = Column(Date, nullable=True)
    added_at = Column(DateTime, default=datetime.now)

# Crear la tabla en la base de datos (si no existe)
Base.metadata.create_all(bind=engine)
