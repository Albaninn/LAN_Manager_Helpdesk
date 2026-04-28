from sqlalchemy import Column, String, DateTime
from datetime import datetime
from .database import Base

class Dispositivo(Base):
    __tablename__ = "dispositivos"

    # Identificador único (MAC Address)
    mac = Column(String, primary_key=True, index=True) 
    
    # Informações de Rede
    ip = Column(String)
    rede_id = Column(String) # Ex: '85.x' ou '200.x'
    status = Column(String)  # up / down / inacessivel
    
    # Identificação Humana
    hostname_real = Column(String)
    apelido = Column(String, nullable=True) # Nome personalizado por você
    
    # Nova Coluna: Categorias / Tags
    # Valor padrão 'Outros' para não vir vazio nos novos scans
    categoria = Column(String, default="Outros") 
    
    # Informações do Hardware
    vendor = Column(String) # Fabricante retornado pelo Nmap
    
    # Datas de Controle
    # default=datetime.now: Horário de criação do registro
    # onupdate=datetime.now: Atualiza automaticamente sempre que o IP ou Status mudar
    ultima_vez_visto = Column(DateTime, default=datetime.now, onupdate=datetime.now)