param(
    [string]$EnvFile
)

. (Join-Path $PSScriptRoot "_common.ps1")

$repoRoot = Get-RepoRoot
$EnvFile = if ($EnvFile) { $EnvFile } else { Join-Path $repoRoot ".env.fabric" }
if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Missing $EnvFile. Run 01-bootstrap-network.ps1 first."
}

Import-DotEnvFile -Path $EnvFile

$gatewayPort = 8080
$appPort = 8000

$gatewayCommand = @"
Set-Location -LiteralPath '$repoRoot'
`$env:LEDGER_BACKEND = 'fabric-direct'
`$env:PYTHONPATH = '$repoRoot'
python -m uvicorn app.fabric_gateway_api:app --host 127.0.0.1 --port $gatewayPort
"@

Write-Host "Starting Fabric gateway API on http://127.0.0.1:$gatewayPort ..."
Start-Process -FilePath powershell -WindowStyle Hidden -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $gatewayCommand
)

$healthUrl = "http://127.0.0.1:$gatewayPort/health"
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

try {
    $health = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5
    Write-Host ("Gateway health: " + $health.Content)
} catch {
    throw "Fabric gateway API did not become ready at $healthUrl"
}

Write-Host "Starting FastAPI app on http://127.0.0.1:$appPort ..."
Set-Location -LiteralPath $repoRoot
$env:LEDGER_BACKEND = "fabric-gateway"
$env:PYTHONPATH = $repoRoot
python -m uvicorn app.main:app --host 127.0.0.1 --port $appPort --reload
