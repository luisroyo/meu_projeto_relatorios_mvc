@echo off
echo ========================================
echo    INICIANDO BACKEND FLASK
echo ========================================
echo.

cd ..\meu_projeto_relatorios_mvc

echo Verificando se o ambiente virtual existe...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate

echo Instalando dependências...
pip install -r requirements.txt

echo Iniciando servidor Flask...
echo.
echo Backend estará disponível em: http://localhost:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python run.py

pause 