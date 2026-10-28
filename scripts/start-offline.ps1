$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelPath = Join-Path $projectRoot '.models\nemotron-3.5-parse'
docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    docker desktop start --timeout 120
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop could not start.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $modelPath 'model.safetensors'))) {
    throw 'Local model files are missing. Complete model setup first.'
}
$existing = docker ps -a --filter 'name=^/docflow-nim-worker$' --format '{{.Names}}'
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop first.' }
if ($existing -eq 'docflow-nim-worker') {
    docker start docflow-nim-worker
} else {
    docker run -d --name docflow-nim-worker --gpus all -p 127.0.0.1:8473:8000 --mount "type=bind,source=$modelPath,target=/model,readonly" docflow-nim-local:dev
}
if ($LASTEXITCODE -ne 0) { throw 'Local worker could not start.' }
Write-Host 'Waiting for the local model to load...'
for ($attempt = 0; $attempt -lt 120; $attempt++) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8473/health' -TimeoutSec 2
        if ($health.ready) { Write-Host 'Local model ready. You can convert documents.'; exit 0 }
    } catch { }
    if ((docker inspect --format '{{.State.Running}}' docflow-nim-worker) -ne 'true') {
        docker logs --tail 20 docflow-nim-worker
        throw 'Local worker stopped during startup.'
    }
    Start-Sleep -Seconds 2
}
throw 'Model startup timed out. Inspect docker logs docflow-nim-worker.'
