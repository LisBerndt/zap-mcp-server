@echo off
setlocal

echo Building ZAP MCP Docker/Podman image...

REM Detect container runtime
where podman >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_RUNTIME=podman
    echo Using Podman as container runtime
    goto :build
)

where docker >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_RUNTIME=docker
    echo Using Docker as container runtime
    goto :build
)

echo Error: Neither Docker nor Podman found!
exit /b 1

:build
REM Build the container image
%CONTAINER_RUNTIME% build -t zap-mcp-server:latest .

echo Build completed successfully!
echo.
echo To run the container:
if "%CONTAINER_RUNTIME%"=="podman" (
    echo   podman-compose up -d
    echo Or manually:
    echo   podman run -p 8080:8080 -p 8082:8082 zap-mcp-server:latest
) else (
    echo   docker-compose up -d
    echo Or manually:
    echo   docker run -p 8080:8080 -p 8082:8082 zap-mcp-server:latest
)

pause



