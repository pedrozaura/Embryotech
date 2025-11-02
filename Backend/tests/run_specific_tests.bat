@echo off
REM Script para executar testes especificos no Windows
REM Uso: run_specific_tests.bat [opcao]

setlocal enabledelayedexpansion

echo ==========================================
echo   EMBRYOTECH - Testes Especificos
echo ==========================================
echo.

REM Mudar para o diretório do script
cd /d %~dp0

REM Verificar argumento
if "%1"=="" (
    echo [ERRO] Nenhuma opcao especificada!
    echo.
    echo Uso: run_specific_tests.bat [opcao]
    echo.
    echo Opcoes:
    echo   models      - Executar apenas testes de modelos
    echo   auth        - Executar apenas testes de autenticacao
    echo   api         - Executar apenas testes de API
    echo   logging     - Executar apenas testes de logging
    echo   parametros  - Executar apenas testes de parametros
    echo   leituras    - Executar apenas testes de leituras
    echo   fast        - Executar apenas testes rapidos
    echo   failed      - Re-executar testes que falharam
    echo   help        - Mostrar esta mensagem
    echo.
    pause
    exit /b 1
)

if /i "%1"=="help" (
    echo Opcoes disponiveis:
    echo   models      - Executar apenas testes de modelos
    echo   auth        - Executar apenas testes de autenticacao
    echo   api         - Executar apenas testes de API
    echo   logging     - Executar apenas testes de logging
    echo   parametros  - Executar apenas testes de parametros
    echo   leituras    - Executar apenas testes de leituras
    echo   fast        - Executar apenas testes rapidos
    echo   failed      - Re-executar testes que falharam
    echo.
    pause
    exit /b 0
)

if /i "%1"=="models" (
    echo [INFO] Executando testes de modelos...
    pytest tests/test_models.py -v
    goto :end
)

if /i "%1"=="auth" (
    echo [INFO] Executando testes de autenticacao...
    pytest tests/test_auth.py -v
    goto :end
)

if /i "%1"=="api" (
    echo [INFO] Executando testes de API...
    pytest tests/test_parametros_api.py tests/test_leituras_api.py -v
    goto :end
)

if /i "%1"=="logging" (
    echo [INFO] Executando testes de logging...
    pytest tests/test_logging.py -v
    goto :end
)

if /i "%1"=="parametros" (
    echo [INFO] Executando testes de parametros...
    pytest tests/test_parametros_api.py -v
    goto :end
)

if /i "%1"=="leituras" (
    echo [INFO] Executando testes de leituras...
    pytest tests/test_leituras_api.py -v
    goto :end
)

if /i "%1"=="fast" (
    echo [INFO] Executando apenas testes rapidos...
    pytest tests/ -v -m "not slow"
    goto :end
)

if /i "%1"=="failed" (
    echo [INFO] Re-executando testes que falharam...
    pytest --lf -v
    goto :end
)

echo [ERRO] Opcao desconhecida: %1
echo Execute "run_specific_tests.bat help" para ver as opcoes
pause
exit /b 1

:end
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCESSO] Testes executados com sucesso!
) else (
    echo.
    echo [FALHA] Alguns testes falharam!
)
pause
