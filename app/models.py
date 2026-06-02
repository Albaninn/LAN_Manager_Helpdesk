from sqlalchemy import Column, String, DateTime
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
    
    # OS TRÊS CAMPOS DE INVENTÁRIO QUE VOCÊ QUERIA (Substituindo a antiga categoria)
    area = Column(String, nullable=True)  # Ex: TI, ADM, RH
    time = Column(String, nullable=True)  # Ex: SUPORTE, INFRA, FINANCEIRO
    tipo = Column(String, nullable=True)  # Ex: NOTEBOOK, DESKTOP, CAMERA
    
    # O CAMPO DO SCANNER QUE REATIVAMOS
    ultima_vez_visto = Column(DateTime, nullable=True)