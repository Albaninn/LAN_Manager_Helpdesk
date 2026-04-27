import nmap
import os
from sqlalchemy.orm import Session
from .models import Dispositivo
from . import models # Import necessário para a query de update
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def scan_network(db: Session):
    # 1. Registra o momento exato em que o scan começou
    horario_inicio_scan = datetime.now()
    print(f"DEBUG: Iniciando ciclo de limpeza. Horário corte: {horario_inicio_scan}")

    # Pega os ranges do .env
    network_ranges = os.getenv("NETWORK_RANGES", "").split()
    
    nm = nmap.PortScanner()
    
    for rede in network_ranges:
        print(f"Iniciando varredura na rede: {rede}...")
        
        # Aumentamos a agressividade: -PR (ARP) e -PS445 (SMB)
        # O --max-retries 1 evita que ele fique "imaginando" que o host existe
        nm.scan(hosts=rede, arguments='-sn -PR -PS445 --max-retries 1 -T4')

        for host in nm.all_hosts():
            try:
                # Coleta dados básicos
                mac = nm[host]['addresses'].get('mac', 'N/A').upper()
                hostname_real = nm[host].hostname() or "Desconhecido"
                vendor = nm[host].get('vendor', {}).get(mac, 'Genérico')
                
                # Identifica a rede
                partes_ip = host.split('.')
                rede_id = f"{partes_ip[2]}.x" if len(partes_ip) > 2 else "Outra"

                # Lógica de UPSERT (Update ou Insert)
                db_device = db.query(Dispositivo).filter(Dispositivo.mac == mac).first()

                if db_device:
                    # Se já existe, atualiza as infos e "carimba" o tempo atual
                    db_device.ip = host
                    db_device.hostname_real = hostname_real
                    db_device.status = "up"
                    db_device.rede_id = rede_id
                    db_device.ultima_vez_visto = datetime.now()
                else:
                    # Se é novo e tem MAC válido
                    if mac != 'N/A':
                        novo_dispositivo = Dispositivo(
                            mac=mac,
                            ip=host,
                            hostname_real=hostname_real,
                            apelido=None, 
                            vendor=vendor,
                            status="up",
                            rede_id=rede_id,
                            ultima_vez_visto=datetime.now()
                        )
                        db.add(novo_dispositivo)
            except Exception as e:
                print(f"Erro ao processar host {host}: {e}")
                continue
        db.commit()
    
    # 2. O FILTRO DA VERDADE
    # Qualquer um que ainda esteja 'up' mas o 'ultima_vez_visto' 
    # é anterior ao 'horario_inicio_scan', COM CERTEZA não foi visto agora.
    afetados = db.query(models.Dispositivo).filter(
        models.Dispositivo.status == "up",
        models.Dispositivo.ultima_vez_visto < horario_inicio_scan
    ).update({"status": "down"})

    db.commit()
    print(f"DEBUG: {afetados} dispositivos foram marcados como OFFLINE.")
    print(f"Scan finalizado. Varredura concluída em {datetime.now() - horario_inicio_scan}")