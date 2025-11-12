#!/bin/bash

echo "================================"
echo "HTTP客户端增强版 - Linux运行脚本"
echo "================================"
echo

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3"
    echo
    echo "请先安装Python3："
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

echo "✓ Python3已安装"
python3 --version
echo

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误：未找到pip3"
    echo
    echo "请安装pip3："
    echo "  sudo apt install python3-pip"
    exit 1
fi

echo "✓ pip3已安装"
echo

# 检查是否有图形界面
if [ -z "$DISPLAY" ]; then
    echo "⚠️  警告：未检测到DISPLAY环境变量"
    echo "  如果在无头服务器上，需要使用X转发或虚拟显示器"
    echo
    echo "  方法1 - 使用ssh X转发："
    echo "    ssh -X username@hostname"
    echo
    echo "  方法2 - 安装虚拟显示器："
    echo "    sudo apt install xvfb"
    echo "    xvfb-run -a python3 http_client_enhanced.py"
    echo
    echo "尝试继续运行..."
    echo
fi

# 安装依赖
echo "步骤1：安装Python依赖包..."
echo
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo
    echo "❌ 依赖安装失败"
    exit 1
fi

echo
echo "✓ 依赖安装完成"
echo

# 检查tkinter
echo "步骤2：检查tkinter..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ tkinter未安装"
    echo
    echo "请安装tkinter："
    echo "  sudo apt install python3-tk"
    exit 1
fi

echo "✓ tkinter已安装"
echo

echo "================================"
echo "准备就绪！正在启动程序..."
echo "================================"
echo

# 运行程序
python3 http_client_enhanced.py
