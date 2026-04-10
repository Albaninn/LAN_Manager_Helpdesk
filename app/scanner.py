import nmap
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() # Carrega o .env
print(f"DEBUG: O range lido do .env foi: {os.getenv('NETWORK_RANGES')}")

def load_known_devices():
    try:
        with open("known_devices.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def scan_network():
    # Pega os ranges do .env, se não existir, usa um padrão seguro
    network_range = os.getenv("NETWORK_RANGES", "127.0.0.1/32")
    known_devices = load_known_devices()
    
    nm = nmap.PortScanner()
    nm.scan(hosts=network_range, arguments='-sn -T4')
    
    devices = []
    for host in nm.all_hosts():
        mac = nm[host]['addresses'].get('mac', 'N/A')
        
        # Busca o nome no JSON, senão tenta o hostname, senão "Desconhecido"
        nome_final = known_devices.get(mac) or nm[host].hostname() or "Desconhecido"
        
        devices.append({
            "ip": host,
            "name": nome_final,
            "mac": mac,
            "vendor": nm[host].get('vendor', {}).get(mac, 'Genérico'),
            "status": nm[host].state()
        })
    return devices
