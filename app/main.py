from fastapi import FastAPI, Request, Depends, BackgroundTasks, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

# Importações internas do seu projeto
from .database import SessionLocal, engine
from . import models
from .scanner import scan_network

# Cria as tabelas na base de dados (database.db) se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

from fastapi import Form

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

# Rota futura para editar o apelido (exemplo de como o ORM facilita)
@app.post("/atualizar_apelido/{mac}")
async def atualizar_apelido(mac: str, novo_apelido: str, db: Session = Depends(get_db)):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        dispositivo.apelido = novo_apelido
        db.commit()
    return {"status": "sucesso"}

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # 1. CONTAGEM REAL (Linhas únicas no banco)
    # Isso evita que dispositivos com múltiplas tags inflem o total
    total_real = db.query(models.Dispositivo).count()

    # 2. Coleta de Status
    stats_raw = db.query(models.Dispositivo.status, func.count(models.Dispositivo.mac)).group_by(models.Dispositivo.status).all()
    stats_status = {str(k): int(v) for k, v in stats_raw}
    
    # 3. Coleta de Tags (Para o gráfico de pizza)
    todos = db.query(models.Dispositivo.categoria).all()
    tags_map = {}
    for d in todos:
        if d[0]:
            for t in str(d[0]).split(','):
                name = t.strip().upper()
                if name: tags_map[name] = tags_map.get(name, 0) + 1

    # 4. Coleta de Fabricantes
    vend_raw = db.query(models.Dispositivo.vendor, func.count(models.Dispositivo.mac)).group_by(models.Dispositivo.vendor).limit(5).all()
    vendors_map = {str(k): int(v) for k, v in vend_raw}

    # 5. RETORNO SEGURO (Mantendo a sintaxe que funcionou no Python 3.14)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_real": total_real,
            "stats_status": stats_status,
            "tags": tags_map,
            "vendors": vendors_map
        }
    )