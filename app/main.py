from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .scanner import scan_network

app = FastAPI()

# Configura onde estão os arquivos HTML
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request):
    # Faz a varredura (ajuste o range para a sua rede se for diferente)
    lista_dispositivos = scan_network() 
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"dispositivos": lista_dispositivos}
    )