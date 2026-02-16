Write-Host "Iniciando Frontend com Node.js Portátil..."
$current = Get-Location
$nodeDir = Join-Path $current "..\node_portable"
$env:PATH = "$nodeDir;$env:PATH"

Write-Host "Node detectado: $(node -v)"
Write-Host "NPM detectado: $(npm -v)"

Write-Host "Iniciando servidor Vite..."
npm run dev
