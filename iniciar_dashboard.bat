@echo off
title Grillato System - Dashboard
echo.
echo ============================================
echo   GRILLATO SYSTEM - Iniciando Dashboard
echo ============================================
echo.

:: Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python em python.org
    pause
    exit /b 1
)

:: Verifica se Streamlit está instalado
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias pela primeira vez...
    echo.
    pip install streamlit pandas win10toast
    echo.
    echo Dependencias instaladas!
    echo.
)

:: Inicia o dashboard
echo Abrindo dashboard no navegador...
echo Para encerrar, feche esta janela ou pressione Ctrl+C
echo.
cd /d "%~dp0"
streamlit run dashboard.py --server.port 8501 --server.headless false --browser.gatherUsageStats false
pause
