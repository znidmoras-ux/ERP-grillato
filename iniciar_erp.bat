@echo off
echo ========================================
echo    GRILLATO ERP - Iniciando...
echo ========================================

REM Verificar Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERRO: Python nao encontrado! Instale: https://python.org
    pause
    exit /b 1
)

REM Instalar dependencias
echo Verificando dependencias...
pip install -q streamlit supabase python-dotenv pandas plotly

REM Verificar .env
if not exist ".env" (
    echo.
    echo ========================================
    echo  CONFIGURACAO NECESSARIA
    echo ========================================
    echo Copie o arquivo .env.example para .env
    echo e preencha SUPABASE_URL e SUPABASE_KEY
    echo ========================================
    copy .env.example .env
    notepad .env
    pause
)

REM Iniciar
echo Abrindo ERP no navegador...
streamlit run erp/app.py --server.port 8501

pause
