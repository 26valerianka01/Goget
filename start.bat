@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === GoGet: старт БД + приложения ===
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo [Ошибка] Docker не найден. Установите Docker Desktop:
  echo https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [Ошибка] Docker Desktop не запущен. Откройте Docker Desktop и дождитесь статуса Running.
  pause
  exit /b 1
)

echo [1/5] Поднимаю MySQL в Docker...
docker compose up -d
if errorlevel 1 (
  echo [Ошибка] docker compose up не удался.
  pause
  exit /b 1
)

echo [2/5] Жду готовности MySQL...
set /a tries=0
:wait_mysql
set /a tries+=1
docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -pgoget --silent >nul 2>nul
if not errorlevel 1 goto mysql_ready
if %tries% geq 40 (
  echo [Ошибка] MySQL не ответил за ~2 минуты. Смотрите: docker compose logs mysql
  pause
  exit /b 1
)
timeout /t 3 /nobreak >nul
goto wait_mysql

:mysql_ready
echo       MySQL готов.

if not exist ".env" (
  echo [3/5] Создаю .env из .env.docker ...
  copy /Y ".env.docker" ".env" >nul
) else (
  echo [3/5] .env уже есть - оставляю как есть.
)

if not exist ".venv\Scripts\python.exe" (
  echo       Создаю виртуальное окружение...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)

echo       Ставлю зависимости...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo [Ошибка] pip install не удался.
  pause
  exit /b 1
)

echo [4/5] Демо-заказы курьера...
".venv\Scripts\python.exe" scripts\seed_courier_demo.py

echo [5/5] Запускаю GoGet...
echo.
".venv\Scripts\python.exe" main.py
pause
