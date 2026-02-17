# Script para iniciar o backend do sistema de gestão de segurança
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   INICIANDO BACKEND - GESTAO SEGURANCA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se estamos no diretório correto (raiz)
if (-not (Test-Path "backend/run.py")) {
    Write-Host "ERRO: Arquivo backend/run.py não encontrado!" -ForegroundColor Red
    Write-Host "Certifique-se de estar na raiz do projeto" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Executar o backend usando o python do ambiente virtual diretamente
Write-Host "[1/2] Iniciando servidor Flask..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   BACKEND RODANDO EM: http://localhost:5000" -ForegroundColor Green
Write-Host "   Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$env:FLASK_APP = "backend/run.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:PYTHONPATH = "$PWD/backend"

& ".\backend\venv\Scripts\python.exe" backend\run.py
