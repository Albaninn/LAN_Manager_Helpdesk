from sqlalchemy import Column, String, DateTime
from datetime import datetime
from .database import Base

class Dispositivo(Base):
    __tablename__ = "dispositivos"

    mac = Column(String, primary_key=True, index=True) # Identificador único
    ip = Column(String)
    hostname_real = Column(String)
    apelido = Column(String, nullable=True) # O nome que você vai editar
    vendor = Column(String)
    status = Column(String) # up / down
    rede_id = Column(String) # Aqui salvamos se é '85.x' ou '200.x'
    ultima_vez_visto = Column(DateTime, default=datetime.now, onupdate=datetime.now)