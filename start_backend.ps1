# Script para iniciar o backend do sistema de gestão de segurança
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   INICIANDO BACKEND - GESTAO SEGURANCA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se estamos no diretório correto
if (-not (Test-Path "run.py")) {
    Write-Host "ERRO: Arquivo run.py não encontrado!" -ForegroundColor Red
    Write-Host "Certifique-se de estar no diretório backend" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Ativar ambiente virtual
Write-Host "[1/3] Ativando ambiente virtual..." -ForegroundColor Green
try {
    & ".\venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao ativar ambiente virtual"
    }
}
catch {
    Write-Host "ERRO: Falha ao ativar ambiente virtual!" -ForegroundColor Red
    Write-Host "Verifique se o ambiente virtual existe: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Verificar dependências
Write-Host "[2/3] Verificando dependências..." -ForegroundColor Green
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar dependências"
    }
}
catch {
    Write-Host "ERRO: Falha ao instalar dependências!" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Executar o backend
Write-Host "[3/3] Iniciando servidor Flask..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   BACKEND RODANDO EM: http://localhost:5000" -ForegroundColor Green
Write-Host "   Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Executar o Flask
python run.py 