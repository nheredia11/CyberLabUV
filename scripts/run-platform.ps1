$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

$ComposeFile = "docker-compose.dev.yml"

Write-Host "[CyberLabUV] Checking Docker Compose..."
try {
    docker compose version | Out-Host
} catch {
    Write-Host "Docker Compose is not available from PowerShell. Open Docker Desktop and verify it is running."
    Write-Host "Then run: docker compose version"
    exit 1
}

Write-Host "[CyberLabUV] Starting platform..."
docker compose -f $ComposeFile up --build
