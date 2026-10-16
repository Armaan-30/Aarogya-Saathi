$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$nodePath = (Get-Command node).Source
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install dependencies first. See README.md.' }
$backendPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$frontendPort = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($backendPort -or $frontendPort) { throw 'Port 8000 or 5173 is in use. Check existing services before starting another copy.' }
$backendProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'backend\server.log') -RedirectStandardError (Join-Path $projectRoot 'backend\server-error.log')
$frontendProcess = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173','--strictPort' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'frontend\server.log') -RedirectStandardError (Join-Path $projectRoot 'frontend\server-error.log')
Write-Host "Backend PID: $($backendProcess.Id); frontend PID: $($frontendProcess.Id)"
Write-Host 'Open http://localhost:5173. API docs: http://localhost:8000/docs'
Write-Host 'Stop these processes with Stop-Process -Id <PID>.'
