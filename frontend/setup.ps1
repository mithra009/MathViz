# Manim AI Frontend - Quick Setup Script
Write-Host " Manim AI Frontend Setup" -ForegroundColor Cyan
Write-Host "=" * 50
Write-Host ""

# Check if Node.js is installed
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host " Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host " Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if npm is installed
Write-Host "Checking npm installation..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host " npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host " npm not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Install npm packages
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" * 50
    Write-Host " Setup complete!" -ForegroundColor Green
    Write-Host "=" * 50
    Write-Host ""
    Write-Host " To start the development server:" -ForegroundColor Cyan
    Write-Host "   npm run dev" -ForegroundColor White
    Write-Host ""
    Write-Host " The app will be available at:" -ForegroundColor Cyan
    Write-Host "   http://localhost:3000" -ForegroundColor White
    Write-Host ""
    Write-Host "  Make sure your backend is running on port 8000!" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host " Installation failed!" -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    Write-Host ""
}
