@echo off
echo ============================
echo HTTP客户端打包工具
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

echo 步骤1：安装依赖包...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误：依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 步骤2：清理之前的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo 步骤3：使用PyInstaller打包...
echo.

REM 尝试使用spec文件打包
pyinstaller --clean http_client.spec >nul 2>&1
if errorlevel 1 (
    echo 尝试使用spec文件失败，尝试直接打包...
    pyinstaller --onefile --windowed --name "HTTP客户端增强版" http_client_enhanced.py
)

echo.
echo ============================
echo 打包完成！
echo ============================
echo.
echo 可执行文件位置：dist\HTTP客户端增强版.exe
echo.
pause
