#!/bin/bash

echo "================================"
echo "HTTP客户端增强版 - 使用虚拟显示器"
echo "================================"
echo

# 检查xvfb
if ! command -v xvfb-run &> /dev/null; then
    echo "❌ 错误：xvfb未安装"
    echo
    echo "请先安装xvfb："
    echo "  sudo apt update"
    echo "  sudo apt install xvfb python3-tk"
    echo
    echo "然后重新运行此脚本"
    exit 1
fi

echo "✓ xvfb已安装"
echo

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3"
    exit 1
fi

echo "✓ Python3已安装"
python3 --version
echo

# 安装依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo
echo "✓ 依赖安装完成"
echo

echo "================================"
echo "使用虚拟显示器启动程序..."
echo "================================"
echo

# 使用xvfb运行程序
xvfb-run -a python3 http_client_enhanced.py
