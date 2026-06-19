from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .database import Base

class Dispositivo(Base):
    __tablename__ = "dispositivos"

    mac = Column(String, primary_key=True, index=True)
    ip = Column(String)
    status = Column(String)
    vendor = Column(String)
    rede_id = Column(String)
    hostname_real = Column(String, nullable=True)
    apelido = Column(String, nullable=True)
    area = Column(String, nullable=True)  
    time = Column(String, nullable=True)  
    tipo = Column(String, nullable=True)  
    ultima_vez_visto = Column(DateTime, nullable=True)

    # Nova relação para facilitar a busca do histórico
    historico = relationship("HistoricoIP", back_populates="dispositivo", cascade="all, delete-orphan")


# --- CLASSE NOVA DE HISTÓRICO ---
class HistoricoIP(Base):
    __tablename__ = "historico_ips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mac = Column(String, ForeignKey("dispositivos.mac", ondelete="CASCADE"))
    ip_antigo = Column(String)
    ip_novo = Column(String)
    data_mudanca = Column(DateTime)

    dispositivo = relationship("Dispositivo", back_populates="historico")