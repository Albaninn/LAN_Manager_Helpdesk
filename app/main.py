from fastapi import FastAPI, Request, Depends, BackgroundTasks
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
async def home(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Opção Pro: Rodar o scan em segundo plano para a página não ficar "pendurada"
    # Assim o utilizador vê o que já está na base de dados imediatamente
    background_tasks.add_task(scan_network, db)
    
    # Procura todos os dispositivos guardados na base de dados
    # Ordenamos por IP para ficar organizado
    dispositivos = db.query(models.Dispositivo).order_by(models.Dispositivo.ip).all()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"dispositivos": dispositivos}
    )

# Rota futura para editar o apelido (exemplo de como o ORM facilita)
@app.post("/atualizar_apelido/{mac}")
async def atualizar_apelido(mac: str, novo_apelido: str, db: Session = Depends(get_db)):
    dispositivo = db.query(models.Dispositivo).filter(models.Dispositivo.mac == mac).first()
    if dispositivo:
        dispositivo.apelido = novo_apelido
        db.commit()
    return {"status": "sucesso"}