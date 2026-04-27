import nmap
import os
from sqlalchemy.orm import Session
from .models import Dispositivo
from . import models
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def scan_network(db: Session):
    # 1. Registra o início do scan
    horario_inicio_scan = datetime.now()
    print(f"\n[SCANNER] Iniciando ciclo. Corte: {horario_inicio_scan.strftime('%H:%M:%S')}")

    network_ranges = os.getenv("NETWORK_RANGES", "").split()
    nm = nmap.PortScanner()
    
    # Lista de IDs de redes configuradas (ex: ['85.x', '200.x'])
    ids_configurados = [f"{r.split('.')[2]}.x" for r in network_ranges if len(r.split('.')) > 2]
    # Lista para rastrear quais IDs responderam com pelo menos 1 host
    ids_alcancaveis = []
    
    for rede in network_ranges:
        print(f"[SCANNER] Varrendo rede: {rede}...")
        
        # Scan agressivo
        nm.scan(hosts=rede, arguments='-sn -PR -PS445 --max-retries 1 -T4')
        
        hosts_encontrados = nm.all_hosts()
        partes_rede = rede.split('.')
        id_atual = f"{partes_rede[2]}.x"

        # Se não achou ninguém, a rede é marcada como inacessível no log e ignorada no loop
        if len(hosts_encontrados) == 0:
            print(f"[WARN] Rede {id_atual} inacessível. Pulando atualização desta rede.")
            continue
            
        ids_alcancaveis.append(id_atual)

        for host in hosts_encontrados:
            try:
                mac = nm[host]['addresses'].get('mac', 'N/A').upper()
                if mac == 'N/A': continue 

                hostname_real = nm[host].hostname() or "Desconhecido"
                vendor = nm[host].get('vendor', {}).get(mac, 'Genérico')
                
                db_device = db.query(Dispositivo).filter(Dispositivo.mac == mac).first()

                if db_device:
                    db_device.ip = host
                    db_device.hostname_real = hostname_real
                    db_device.status = "up"
                    db_device.rede_id = id_atual
                    db_device.ultima_vez_visto = datetime.now()
                else:
                    novo_dispositivo = Dispositivo(
                        mac=mac, ip=host, hostname_real=hostname_real,
                        apelido=None, vendor=vendor, status="up",
                        rede_id=id_atual, ultima_vez_visto=datetime.now()
                    )
                    db.add(novo_dispositivo)
            except Exception as e:
                print(f"Erro ao processar host {host}: {e}")
        
        db.commit()

    # 2. LIMPEZA INTELIGENTE (O DIFERENCIAL)
    for id_rede in ids_configurados:
        if id_rede in ids_alcancaveis:
            # Situação A: A rede está visível. Quem não respondeu agora está realmente DOWN (OFF).
            afetados = db.query(models.Dispositivo).filter(
                models.Dispositivo.status != "down",
                models.Dispositivo.rede_id == id_rede,
                models.Dispositivo.ultima_vez_visto < horario_inicio_scan
            ).update({"status": "down"}, synchronize_session=False)
            
            if afetados > 0:
                print(f"[CLEANUP] {afetados} dispositivos em {id_rede} marcados como OFF.")
        else:
            # Situação B: A rede NÃO foi alcançada. Quem era 'up' ou 'down' agora é 'inacessivel'.
            # Isso evita que você ache que um PC desligou só porque você trocou de cabo.
            afetados = db.query(models.Dispositivo).filter(
                models.Dispositivo.status == "up",
                models.Dispositivo.rede_id == id_rede
            ).update({"status": "inacessivel"}, synchronize_session=False)
            
            if afetados > 0:
                print(f"[CLEANUP] {afetados} dispositivos em {id_rede} marcados como INACESSÍVEL.")

    db.commit()
    print(f"[SCANNER] Ciclo finalizado em {datetime.now() - horario_inicio_scan}\n")