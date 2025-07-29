@echo off
setlocal
chcp 65001

echo ======================================================
echo  Docker Compose 删除脚本
echo ======================================================
echo.

set "WORK_DIR=%~dp0"
set "DOCKER_DIR=%WORK_DIR%..\docker"

REM --- 检查 Docker 是否正在运行 ---
echo [+] 正在检查 Docker Desktop 状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker Desktop 未运行或未响应。
    echo [+] 正在尝试启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    echo [+] 等待 Docker Desktop 启动, 请稍候...
    echo     (这可能需要一到两分钟)

    :wait_for_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        goto wait_for_docker
    )
    echo [+] Docker Desktop 已成功启动！
) else (
    echo [+] Docker Desktop 正在运行。
)

echo.
echo ======================================================
echo.
echo [+] 在`%DOCKER_DIR%`目录执行 docker compose down
cd /d "%DOCKER_DIR%"
docker compose down

echo.
echo ======================================================
echo [+] 脚本执行完毕。
echo ======================================================
echo.
REM pause