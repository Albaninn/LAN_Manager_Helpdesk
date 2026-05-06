from fastapi import FastAPI, Request, Depends, BackgroundTasks, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import logging
import pandas as pd
from io import BytesIO
from datetime import datetime

# Importações internas do seu projeto
from .database import SessionLocal, engine
from . import models
from .scanner import scan_network

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(
    filename='scanner_rede.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cria as tabelas na base de dados (database.db) se não existirem
models.Base.metadata.create_all(bind=engine)

# --- TAREFA AGENDADA (SCANNER AUTOMÁTICO) ---
def tarefa_scan_automatico():
    """Executa a varredura sem travar o app a cada 5 minutos"""
    db = SessionLocal()
    try:
        logging.info("🕒 Automação: Iniciando varredura agendada...")
        scan_network(db)
        logging.info("✅ Automação: Varredura concluída com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro na varredura automática: {e}")
    finally:
        db.close()

# --- GERENCIADOR DE CICLO DE VIDA (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o agendador ao ligar o servidor
    scheduler = BackgroundScheduler()
    scheduler.add_job(tarefa_scan_automatico, 'interval', minutes=5)
    scheduler.start()
    logging.info("🚀 Servidor e Agendador (5min) iniciados.")
    yield
    # Desliga ao encerrar o servidor
    scheduler.shutdown()
    logging.info("🛑 Servidor e Agendador desligados.")

# Inicialização do App
app = FastAPI(lifespan=lifespan)

# Configuração de templates
templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None

# Dependência para obter a sessão da base de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request, background_tasks: BackgroundTasks, filtro: str = None, db: Session = Depends(get_db)):
    print("[DEBUG] Rota HOME acessada. Iniciando scan síncrono...")
    
    background_tasks.add_task(scan_network, db)
    
    query = db.query(models.Dispositivo)
    
    if filtro == "online":
        query = query.filter(models.Dispositivo.status == "up")
    elif filtro == "cadastrados":
        # Filtra apenas os que possuem apelido preenchido
        query = query.filter(models.Dispositivo.apelido != None)
    
    dispositivos = query.order_by(models.Dispositivo.ip).all()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"dispositivos": dispositivos, "filtro_atual": filtro}
    )

@app.post("/salvar_apelido")
async def salvar_apelido(
    mac: str = Form(...), 
    apelido: str = Form(...), 
    categorias: list[str] = Form(...),
    db: Session = Depends(get_db)
):
    print(f"[DEBUG] Salvando Ativo: {mac} | Nome: {apelido} | Cat: {categorias}")
    try:
        # Busca o dispositivo no banco pelo MAC
        dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
        
        if dispositivo:
            dispositivo.apelido = apelido
            dispositivo.categoria = ",".join(categorias)
            db.commit()
            print(f"[SUCCESS] Apelido '{apelido}' salvo com sucesso!")
        else:
            print(f"[ERROR] Dispositivo com MAC {mac} não encontrado no banco.")
            
    except Exception as e:
        print(f"[CRITICAL ERROR] Falha ao salvar no banco: {e}")
        db.rollback() # Desfaz qualquer erro para não travar o banco
        
    return RedirectResponse(url="/", status_code=303)

@app.post("/atualizar_apelido/{mac}")
async def atualizar_apelido(
    mac: str, 
    novo_apelido: str = Form(...), 
    novas_categorias: list[str] = Form(...), 
    db: Session = Depends(get_db)
):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        try:
            dispositivo.apelido = novo_apelido
            dispositivo.categoria = ",".join(novas_categorias)
            db.commit()
            logging.info(f"✏️ Editado: {mac} agora é '{novo_apelido}'")
        except Exception as e:
            db.rollback()
            logging.error(f"❌ Erro ao editar {mac}: {e}")
            
    # Redireciona de volta para a Home para você ver a mudança
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    dispositivos = db.query(models.Dispositivo).all()
    lista_json = [
        {
            "ip": d.ip, "status": d.status, "mac": d.mac,
            "categoria": d.categoria if d.categoria else "",
            "vendor": d.vendor if d.vendor else "Desconhecido",
            "rede_id": d.rede_id
        } for d in dispositivos
    ]
    
    stats_status = {
        "up": len([d for d in lista_json if d['status'] == 'up']),
        "down": len([d for d in lista_json if d['status'] != 'up'])
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_real": len(lista_json),
            "stats_status": stats_status,
            "dispositivos_json": json.dumps(lista_json)
        }
    )

# --- NOVAS ROTAS DE BACKUP E LOGS ---

@app.get("/backup/exportar")
async def exportar_dados(db: Session = Depends(get_db)):
    dispositivos = db.query(models.Dispositivo).all()
    dados = [{
        "MAC": d.mac,
        "IP": d.ip,
        "APELIDO": d.apelido,
        "CATEGORIA": d.categoria,
        "VENDOR": d.vendor
    } for d in dispositivos]
    
    df = pd.DataFrame(dados)
    stream = BytesIO()
    # Exporta com ponto e vírgula e encoding para Excel
    df.to_csv(stream, index=False, encoding='utf-8-sig', sep=';')
    
    headers = {
        'Content-Disposition': f'attachment; filename="backup_lan_{datetime.now().strftime("%Y%m%d")}.csv"'
    }
    return StreamingResponse(BytesIO(stream.getvalue()), media_type="text/csv", headers=headers)

@app.post("/backup/importar")
async def importar_dados(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents), sep=';')
        
        atualizados = 0
        for _, row in df.iterrows():
            disp = db.query(models.Dispositivo).filter(models.Dispositivo.mac == row['MAC']).first()
            if disp:
                if pd.notna(row['APELIDO']): disp.apelido = row['APELIDO']
                if pd.notna(row['CATEGORIA']): disp.categoria = row['CATEGORIA']
                atualizados += 1
        
        db.commit()
        return {"status": "sucesso", "message": f"{atualizados} dispositivos sincronizados."}
    except Exception as e:
        return {"status": "erro", "message": str(e)}

@app.get("/logs/visualizar")
async def visualizar_logs():
    if not os.path.exists('scanner_rede.log'):
        return {"message": "Sem logs ainda."}
    with open('scanner_rede.log', 'r') as f:
        # Retorna as últimas 100 linhas
        return {"historico": f.readlines()[-100:]}