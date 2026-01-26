# Manim AI Service - Start Server Script
# This script loads environment variables from .env and starts the FastAPI server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Manim AI Video Generation Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Load environment variables from .env file
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    Write-Host "Loading environment from .env file..." -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host " Environment variables loaded" -ForegroundColor Green
} else {
    Write-Host " Warning: .env file not found at $envFile" -ForegroundColor Yellow
    Write-Host "  Copy .env.example to .env and fill in your credentials" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting server on http://localhost:7860" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn src.manim_service.app:app --host 0.0.0.0 --port 7860 --reload
