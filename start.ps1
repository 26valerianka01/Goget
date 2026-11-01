# GoGet one-click: Docker MySQL + приложение
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== GoGet: старт БД + приложения ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker не найден. Установите Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}

docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Desktop не запущен. Откройте его и дождитесь статуса Running." -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] docker compose up -d"
docker compose up -d

Write-Host "[2/5] Ожидание MySQL..."
$ok = $false
for ($i = 1; $i -le 40; $i++) {
    docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -pgoget --silent 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ok) {
    Write-Host "MySQL не поднялся. Логи: docker compose logs mysql" -ForegroundColor Red
    exit 1
}
Write-Host "      MySQL готов." -ForegroundColor Green

if (-not (Test-Path ".env")) {
    Copy-Item ".env.docker" ".env" -Force
    Write-Host "[3/5] Создан .env из .env.docker"
} else {
    Write-Host "[3/5] .env уже есть"
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "      Создаю .venv..."
    python -m venv .venv
}

Write-Host "      pip install..."
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt

Write-Host "[4/5] Демо-заказы курьера (идемпотентно)..."
& .\.venv\Scripts\python.exe scripts\seed_courier_demo.py

Write-Host "[5/5] Запуск main.py" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe main.py
