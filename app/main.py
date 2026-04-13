from fastapi import FastAPI, Request, Depends, BackgroundTasks, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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
async def home(request: Request, rede: str = None, db: Session = Depends(get_db)):
    # Busca os dispositivos
    query = db.query(models.Dispositivo)
    
    # Se clicar no filtro, filtramos a query
    if rede:
        query = query.filter(models.Dispositivo.rede_id == rede)
    
    dispositivos = query.order_by(models.Dispositivo.ip).all()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"dispositivos": dispositivos, "rede_atual": rede}
    )

from fastapi import Form

@app.post("/salvar_apelido")
async def salvar_apelido(mac: str = Form(...), apelido: str = Form(...), db: Session = Depends(get_db)):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        dispositivo.apelido = apelido
        db.commit()
    return RedirectResponse(url="/", status_code=303)

# Rota futura para editar o apelido (exemplo de como o ORM facilita)
@app.post("/atualizar_apelido/{mac}")
async def atualizar_apelido(mac: str, novo_apelido: str, db: Session = Depends(get_db)):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        dispositivo.apelido = novo_apelido
        db.commit()
    return {"status": "sucesso"}