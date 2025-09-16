@echo off
setlocal

echo Starting ZAP MCP Server...

REM Detect container runtime
where podman >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_RUNTIME=podman
    set COMPOSE_CMD=podman-compose
    echo Using Podman as container runtime
    goto :start
)

where docker >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_RUNTIME=docker
    set COMPOSE_CMD=docker-compose
    echo Using Docker as container runtime
    goto :start
)

echo Error: Neither Docker nor Podman found!
exit /b 1

:start
REM Start with compose
%COMPOSE_CMD% up -d

echo ZAP MCP Server is starting...
echo ZAP API will be available at: http://localhost:8080
echo MCP Server will be available at: http://localhost:8082/mcp
echo.
echo For localhost scans, use: http://host.docker.internal:PORT
echo.
echo To view logs: %COMPOSE_CMD% logs -f
echo To stop: %COMPOSE_CMD% down

pause



