from fastapi import FastAPI, Request, Depends, BackgroundTasks, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import json
import logging
import pandas as pd
from io import BytesIO
from datetime import datetime

import sys
import os

# Força o Python a enxergar a pasta raiz do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models
from app.scanner import scan_network

logging.basicConfig(
    filename='scanner_rede.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

models.Base.metadata.create_all(bind=engine)

def tarefa_scan_automatico():
    db = SessionLocal()
    try:
        logging.info("🕒 Automação: Varredura de 5 minutos iniciada...")
        scan_network(db)
        logging.info("✅ Automação: Varredura concluída com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro na varredura automática: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(tarefa_scan_automatico, 'interval', minutes=5)
    scheduler.start()
    logging.info("🚀 Servidor e Agendador de Inventário Iniciados.")
    yield
    scheduler.shutdown()
    logging.info("🛑 Servidor e Agendador desligados.")

app = FastAPI(lifespan=lifespan)

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request, filtro: str = None, db: Session = Depends(get_db)):
    print("[DEBUG] Rota HOME acessada.")
    query = db.query(models.Dispositivo)

    if filtro == "online":
        query = query.filter(models.Dispositivo.status == "up")
    elif filtro == "cadastrados":
        query = query.filter(models.Dispositivo.apelido != None)
    
    dispositivos = query.order_by(models.Dispositivo.ip).all()
    areas_existentes = [r[0] for r in db.query(func.distinct(models.Dispositivo.area)).all() if r[0] and r[0] != "N/A"]
    times_existentes = [r[0] for r in db.query(func.distinct(models.Dispositivo.time)).all() if r[0] and r[0] != "N/A"]
    tipos_existentes = [r[0] for r in db.query(func.distinct(models.Dispositivo.tipo)).all() if r[0] and r[0] != "N/A"]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "dispositivos": dispositivos, 
            "filtro_atual": filtro,
            "areas_disponiveis": sorted(areas_existentes),
            "times_disponiveis": sorted(times_existentes),
            "tipos_disponiveis": sorted(tipos_existentes)
        }
    )


@app.get("/scan_manual")
async def scan_manual(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logging.info("⚡ Scan Manual solicitado via interface.")
    background_tasks.add_task(scan_network, db)
    return RedirectResponse(url="/", status_code=303)

@app.post("/salvar_apelido")
async def salvar_apelido(
    mac: str = Form(...), 
    apelido: str = Form(...), 
    area: str = Form(None),
    time: str = Form(None),
    tipo: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
        if dispositivo:
            dispositivo.apelido = apelido
            dispositivo.area = area.strip().upper() if area else "N/A"
            dispositivo.time = time.strip().upper() if time else "N/A"
            dispositivo.tipo = tipo.strip().upper() if tipo else "N/A"
            db.commit()
            logging.info(f"💾 Salvo Ativo {mac}: Área={area} | Time={time} | Tipo={tipo}")
    except Exception as e:
        logging.error(f"❌ Erro ao salvar apelido: {e}")
        db.rollback()
    return RedirectResponse(url="/", status_code=303)

@app.post("/atualizar_apelido/{mac}")
async def atualizar_apelido(
    mac: str, 
    novo_apelido: str = Form(...), 
    nova_area: str = Form(None), 
    novo_time: str = Form(None),
    novo_tipo: str = Form(None), 
    db: Session = Depends(get_db)
):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        try:
            dispositivo.apelido = novo_apelido
            dispositivo.area = nova_area.strip().upper() if nova_area else "N/A"
            dispositivo.time = novo_time.strip().upper() if novo_time else "N/A"
            dispositivo.tipo = novo_tipo.strip().upper() if novo_tipo else "N/A"
            db.commit()
            logging.info(f"✏️ Atualizado {mac}: Área={nova_area} | Time={novo_time} | Tipo={novo_tipo}")
        except Exception as e:
            db.rollback()
            logging.error(f"❌ Erro ao editar {mac}: {e}")
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    dispositivos = db.query(models.Dispositivo).all()
    lista_json = [
        {
            "ip": d.ip, "status": d.status, "mac": d.mac,
            "area": d.area if d.area else "N/A",
            "time": d.time if d.time else "N/A",
            "tipo": d.tipo if d.tipo else "N/A",
            "vendor": d.vendor if d.vendor else "Desconhecido",
            "rede_id": d.rede_id
        } for d in dispositivos
    ]
    stats_status = {
        "up": len([d for d in lista_json if d['status'] == 'up']),
        "down": len([d for d in lista_json if d['status'] != 'up'])
    }
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "total_real": len(lista_json), "stats_status": stats_status, "dispositivos_json": json.dumps(lista_json)
    })

@app.get("/backup/exportar")
async def exportar_dados(db: Session = Depends(get_db)):
    dispositivos = db.query(models.Dispositivo).all()
    dados = [{
        "MAC": d.mac, "IP": d.ip, "APELIDO": d.apelido,
        "AREA": d.area, "TIME": d.time, "TIPO": d.tipo, "VENDOR": d.vendor
    } for d in dispositivos]
    
    df = pd.DataFrame(dados)
    stream = BytesIO()
    df.to_csv(stream, index=False, encoding='utf-8-sig', sep=';')
    headers = {'Content-Disposition': f'attachment; filename="backup_lan_{datetime.now().strftime("%Y%m%d")}.csv"'}
    return StreamingResponse(BytesIO(stream.getvalue()), media_type="text/csv", headers=headers)

@app.post("/backup/importar")
async def importar_dados(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents), sep=';')
        if df.empty or 'MAC' not in df.columns:
             return {"status": "erro", "message": "Arquivo ou colunas inválidas."}

        atualizados = 0
        for _, row in df.iterrows():
            disp = db.query(models.Dispositivo).filter(models.Dispositivo.mac == row['MAC']).first()
            if disp:
                if pd.notna(row['APELIDO']): disp.apelido = row['APELIDO']
                if 'AREA' in df.columns and pd.notna(row['AREA']): disp.area = str(row['AREA']).upper()
                if 'TIME' in df.columns and pd.notna(row['TIME']): disp.time = str(row['TIME']).upper()
                if 'TIPO' in df.columns and pd.notna(row['TIPO']): disp.tipo = str(row['TIPO']).upper()
                atualizados += 1
        db.commit()
        logging.info(f"📥 Importação Completa: {atualizados} ativos sincronizados via CSV.")
        return {"status": "sucesso", "message": f"{atualizados} ativos sincronizados."}
    except Exception as e:
        logging.error(f"❌ Falha crítica ao importar backup: {e}")
        return {"status": "erro", "message": str(e)}

@app.get("/logs/visualizar")
async def visualizar_logs():
    if not os.path.exists('scanner_rede.log'):
        return {"message": "Nenhum log gerado."}
    with open('scanner_rede.log', 'r', encoding='utf-8', errors='replace') as f:
        return {"historico": f.readlines()[-100:]}
    
@app.get("/dispositivo/historico/{mac}")
async def obter_historico_dispositivo(mac: str, db: Session = Depends(get_db)):
    registros = db.query(models.HistoricoIP).filter(models.HistoricoIP.mac == mac).order_by(models.HistoricoIP.data_mudanca.desc()).all()
    return [
        {
            "ip_antigo": r.ip_antigo,
            "ip_novo": r.ip_novo,
            "data": r.data_mudanca.strftime("%d/%m/%Y %H:%M:%S")
        } for r in registros
    ]

if __name__ == "__main__":
    import uvicorn
    import threading
    import webview
    import time

    # 1. Função para rodar o backend FastAPI em background
    def rodar_servidor():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

    # Inicia o servidor em paralelo
    server_thread = threading.Thread(target=rodar_servidor, daemon=True)
    server_thread.start()

    # Pausa rápida de 1 segundo para o FastAPI estabilizar as rotas
    time.sleep(1)

    # 2. Abre a janela desktop nativa do Windows espelhando a interface
    webview.create_window(
        title="LAN Manager & Helpdesk", 
        url="http://127.0.0.1:8000",
        width=1280, 
        height=800,
        resizable=True
    )
    
    # Executa a renderização da janela (bloqueante)
    webview.start()