@echo off
echo Starting Nimbus Platform...

echo Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not running
    echo Please install Docker Desktop and make sure it's running
    pause
    exit /b 1
)

echo Building and starting services...
docker-compose up --build -d

echo Waiting for services to start...
timeout /t 10 /nobreak >nul

echo Testing services...
echo.
echo Testing Text Service directly:
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"text\": \"Hello Nimbus!\"}"

echo.
echo Testing Gateway:
curl -X POST http://localhost:8080/api/v1/text/process -H "Content-Type: application/json" -d "{\"text\": \"Hello via Gateway!\"}"

echo.
echo Services are running:
echo - Text Service: http://localhost:8001
echo - Gateway: http://localhost:8080
echo - Redis: localhost:6379
echo - PostgreSQL: localhost:5432

echo.
echo To stop services: docker-compose down
pause