@echo off
REM Script para executar testes no Windows
REM Coloque este arquivo no diretório Backend (onde está app.py)

echo ==========================================
echo   EMBRYOTECH - Execucao de Testes
echo ==========================================
echo.

REM Mudar para o diretório do script
cd /d %~dp0

REM Verificar se pytest está instalado
pytest --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] pytest nao esta instalado!
    echo.
    echo Instale as dependencias com:
    echo   pip install -r requirements-test.txt
    echo.
    pause
    exit /b 1
)

echo [INFO] Iniciando testes...
echo.

REM Executar testes com cobertura
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

REM Verificar resultado
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo   SUCESSO! Todos os testes passaram!
    echo ==========================================
    echo.
    echo Relatorios gerados:
    echo   - HTML: htmlcov\index.html
    echo.
    echo Deseja abrir o relatorio HTML? (S/N)
    choice /C SN /N
    if !ERRORLEVEL! EQU 1 (
        start htmlcov\index.html
    )
) else (
    echo.
    echo ==========================================
    echo   FALHA! Alguns testes falharam!
    echo ==========================================
    echo.
)

pause
