import nmap
import os
from sqlalchemy.orm import Session
from .models import Dispositivo
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def scan_network(db: Session):
    # Pega os ranges do .env
    network_ranges = os.getenv("NETWORK_RANGES", "").split()
    
    nm = nmap.PortScanner()
    
    for rede in network_ranges:
        print(f"Escaneando rede: {rede}...")
        # -sn: Ping Scan (mais rápido)
        nm.scan(hosts=rede, arguments='-sn -T4')
        
        for host in nm.all_hosts():
            # Coleta dados básicos
            mac = nm[host]['addresses'].get('mac', 'N/A').upper()
            hostname_real = nm[host].hostname() or "Desconhecido"
            vendor = nm[host].get('vendor', {}).get(mac, 'Genérico')
            
            # Identifica a rede (ex: extrai '85.x' do IP para o filtro)
            # Se o IP for 192.168.85.15, a rede_id vira '85.x'
            partes_ip = host.split('.')
            rede_id = f"{partes_ip[2]}.x" if len(partes_ip) > 2 else "Outra"

            # Lógica de UPSERT (Update ou Insert)
            db_device = db.query(Dispositivo).filter(Dispositivo.mac == mac).first()

            if db_device:
                # Se já existe, atualiza as infos mutáveis
                db_device.ip = host
                db_device.hostname_real = hostname_real
                db_device.status = "up"
                db_device.rede_id = rede_id
                db_device.ultima_vez_visto = datetime.now()
            else:
                # Se é novo e tem MAC (ignora o próprio PC se vir sem MAC)
                if mac != 'N/A':
                    novo_dispositivo = Dispositivo(
                        mac=mac,
                        ip=host,
                        hostname_real=hostname_real,
                        apelido=None, # Fica vazio para você editar depois
                        vendor=vendor,
                        status="up",
                        rede_id=rede_id
                    )
                    db.add(novo_dispositivo)
        
    db.commit()

    # Opcional: Marcar como 'down' quem não foi visto nesta varredura total
    # (Pode ser feito comparando o timestamp de ultima_vez_visto)