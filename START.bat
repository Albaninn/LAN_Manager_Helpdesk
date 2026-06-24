@echo off
title LAN MANAGER PRO - DESKTOP APP
cls

echo ===================================================
echo   INICIALIZANDO ECOSSISTEMA DO INVENTARIO
echo ===================================================

:: 1. AUTO-INSTALAÇÃO DE REQUISITOS
if exist requirements.txt (
    echo Verificando e instalando dependencias pendentes...
    python -m pip install -r requirements.txt --quiet
    echo ✅ Modulos validados com sucesso!
) else (
    echo [AVISO] requirements.txt nao encontrado. Pulando checagem.
)

echo ---------------------------------------------------

:: 2. DESCOBRIR REDE E INJETAR NO PYTHON
echo Descobrindo a rede ativa local...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"Endereço IPv4"') do (
    set "MY_IP=%%a"
)
set "MY_IP=%MY_IP: =%"

for /f "tokens=1,2,3 delims=." %%a in ("%MY_IP%") do (
    set "CURRENT_NETWORK=%%a.%%b.%%c.0/24"
)
echo Rede identificada: %CURRENT_NETWORK%
set NETWORK_RANGES=%CURRENT_NETWORK%

echo ---------------------------------------------------

:: 3. CRIAÇÃO AUTOMÁTICA DO ATALHO DE INICIALIZAÇÃO COM O WINDOWS
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\LAN_Manager.url"

if not exist "%SHORTCUT_PATH%" (
    echo Configurando para iniciar automaticamente com o Windows...
    echo [InternetShortcut] > "%SHORTCUT_PATH%"
    echo URL=file:///%~dp0START.bat >> "%SHORTCUT_PATH%"
    echo IconIndex=0 >> "%SHORTCUT_PATH%"
    echo ✅ Inicializacao automatica ativada!
)

echo ---------------------------------------------------
echo Abrindo a Janela do Aplicativo...
python app/main.py