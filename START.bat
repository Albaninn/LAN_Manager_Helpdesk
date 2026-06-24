@echo off
title LAN MANAGER PRO - DESKTOP APP
cls

echo ===================================================
echo   INICIALIZANDO ECOSSISTEMA DO INVENTARIO
echo ===================================================

cd /d "%~dp0"

:: 1. AUTO-INSTALAÇÃO DE REQUISITOS
if exist requirements.txt (
    echo Verificando e instalando dependencias pendentes...
    python -m pip install -r requirements.txt --quiet
    echo ✅ Modulos validados com sucesso!
) else (
    echo [AVISO] requirements.txt nao encontrado. Pulando checagem.
)

echo ---------------------------------------------------

:: 2. DESCOBRIR REDE USANDO POWERSHELL (EVITA ERROS DE IDIOMA E ACENTOS)
echo Descobrindo a rede ativa local...

for /f "tokens=*" %%i in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.InterfaceAlias -notlike '*Loopback*'}).IPAddress | Select-Object -First 1"') do set MY_IP=%%i

for /f "tokens=1,2,3 delims=." %%a in ("%MY_IP%") do (
    set "CURRENT_NETWORK=%%a.%%b.%%c.0/24"
)

echo Rede identificada: %CURRENT_NETWORK%
set NETWORK_RANGES=%CURRENT_NETWORK%

echo ---------------------------------------------------
echo Abrindo a Janela do Aplicativo...

python app/main.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Ocorreu um erro ao iniciar o Python. Verifique os logs acima.
    pause
)