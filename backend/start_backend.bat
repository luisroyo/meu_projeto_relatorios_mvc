@echo off
echo ========================================
echo    INICIANDO BACKEND - GESTAO SEGURANCA
echo ========================================
echo.

REM Verificar se estamos no diretório correto
if not exist "backend\run.py" (
    echo ERRO: Arquivo run.py nao encontrado!
    echo Certifique-se de estar no diretório backend
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo [1/3] Ativando ambiente virtual...
call backend\venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual!
    echo Verifique se o ambiente virtual existe: python -m venv venv
    pause
    exit /b 1
)

REM Verificar dependências
echo [2/3] Verificando dependências...
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependências!
    pause
    exit /b 1
)

REM Executar o backend
echo [3/3] Iniciando servidor Flask...
echo.
echo ========================================
echo    BACKEND RODANDO EM: http://localhost:5000
echo    Pressione Ctrl+C para parar
echo ========================================
echo.

python backend\run.py

pause 
