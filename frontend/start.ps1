$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep 3

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Frontend'; npm run dev -- --host"

Write-Host "Both servers are starting..."
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
