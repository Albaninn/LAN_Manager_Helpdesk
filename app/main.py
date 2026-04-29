from fastapi import FastAPI, Request, Depends, BackgroundTasks, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session
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
    # 1. Estatísticas de Status (Online vs Offline)
    stats_status = db.query(models.Dispositivo.status, func.count(models.Dispositivo.mac)) \
                     .group_by(models.Dispositivo.status).all()
    
    # 2. Distribuição por Categorias (Tags)
    # Como salvamos "Notebook,TI", precisamos processar isso
    todos_dispositivos = db.query(models.Dispositivo.categoria).all()
    contagem_tags = {}
    for d in todos_dispositivos:
        if d.categoria:
            for tag in d.categoria.split(','):
                tag = tag.strip().upper()
                contagem_tags[tag] = contagem_tags.get(tag, 0) + 1

    # 3. Top 5 Fabricantes
    top_vendors = db.query(models.Dispositivo.vendor, func.count(models.Dispositivo.mac)) \
                    .group_by(models.Dispositivo.vendor) \
                    .order_by(func.count(models.Dispositivo.mac).desc()).limit(5).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats_status": dict(stats_status),
        "tags": contagem_tags,
        "vendors": dict(top_vendors)
    })