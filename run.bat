@echo off
echo ============================
echo HTTP客户端增强版工具
echo ============================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在启动HTTP客户端增强版工具...
echo.

REM 运行程序
python http_client_enhanced.py

REM 如果程序退出，显示提示
if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)
