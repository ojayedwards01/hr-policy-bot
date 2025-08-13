@echo off
echo ===================================
echo HR Bot Docker Build and Run Script
echo ===================================

echo.
echo [1/4] Building optimized Docker image...
docker build -t hr-bot:latest .

echo.
echo [2/4] Checking image size...
docker images hr-bot:latest

echo.
echo [3/4] Stopping any existing containers...
docker stop hr-bot 2>nul
docker rm hr-bot 2>nul

echo.
echo [4/4] Starting new container...
docker run -d --name hr-bot -p 8080:8080 ^
  -e GROQ_API_KEY="%GROQ_API_KEY%" ^
  -e ENV_MODE="production" ^
  hr-bot:latest

echo.
echo Container started! Access at http://localhost:8080
echo To view logs: docker logs -f hr-bot
