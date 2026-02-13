Write-Host "========================================" -ForegroundColor Green
Write-Host "    INICIANDO BACKEND FLASK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location "..\meu_projeto_relatorios_mvc"

Write-Host "Verificando se o ambiente virtual existe..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Iniciando servidor Flask..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend estará disponível em: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Red
Write-Host ""

python run.py 