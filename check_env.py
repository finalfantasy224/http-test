#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux环境检查脚本
检查运行HTTP客户端所需的环境和依赖
"""

import sys
import subprocess

def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}\n")

def print_result(ok, message):
    status = "✅" if ok else "❌"
    print(f"{status} {message}")

def check_python():
    print_header("Python检查")
    version = sys.version
    print(f"Python版本: {version.split()[0]}")
    if sys.version_info >= (3, 7):
        print_result(True, f"Python版本符合要求 (>= 3.7)")
    else:
        print_result(False, f"Python版本过低，需要 >= 3.7")
    return sys.version_info >= (3, 7)

def check_pip():
    print_header("pip检查")
    try:
        import pip
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_result(True, f"pip可用: {result.stdout.strip()}")
            return True
    except Exception as e:
        pass
    print_result(False, "pip不可用或未安装")
    print("  安装命令: sudo apt install python3-pip")
    return False

def check_tkinter():
    print_header("tkinter检查")
    try:
        import tkinter
        print_result(True, "tkinter已安装")
        print(f"  tkinter版本: {tkinter.TkVersion}")
        return True
    except ImportError:
        print_result(False, "tkinter未安装")
        print("  安装命令: sudo apt install python3-tk")
        return False

def check_requests():
    print_header("requests库检查")
    try:
        import requests
        print_result(True, f"requests已安装 (版本: {requests.__version__})")
        return True
    except ImportError:
        print_result(False, "requests未安装")
        print("  安装命令: pip3 install requests")
        return False

def check_display():
    print_header("图形界面检查")
    import os
    display = os.environ.get('DISPLAY')
    if display:
        print_result(True, f"DISPLAY环境变量已设置: {display}")
        return True
    else:
        print_result(False, "DISPLAY环境变量未设置")
        print("  解决方案:")
        print("    1. 使用图形界面登录")
        print("    2. SSH连接时使用: ssh -X user@host")
        print("    3. 使用虚拟显示器: xvfb-run python3 http_client_enhanced.py")
        return False

def check_xvfb():
    print_header("xvfb检查（虚拟显示器）")
    result = subprocess.run(["which", "xvfb-run"], capture_output=True, text=True)
    if result.returncode == 0:
        print_result(True, "xvfb已安装")
        return True
    else:
        print_result(False, "xvfb未安装")
        print("  安装命令: sudo apt install xvfb")
        return False

def main():
    print("\n" + "="*50)
    print("  HTTP客户端 - Linux环境检查")
    print("="*50)

    checks = {
        "Python": check_python(),
        "pip": check_pip(),
        "tkinter": check_tkinter(),
        "requests": check_requests(),
        "DISPLAY": check_display(),
    }

    print_header("检查总结")
    all_ok = all(checks.values())

    if all_ok:
        print("✅ 所有检查通过！可以运行HTTP客户端增强版")
        print("\n启动命令:")
        print("  python3 http_client_enhanced.py")
        print("\n或使用演示脚本:")
        print("  ./demo_enhanced.sh")
    else:
        print("⚠️  部分检查未通过")
        print("\n根据上述提示安装缺失的组件后，再次运行此脚本")
        print("\n推荐的修复步骤:")
        print("  1. sudo apt update")
        print("  2. sudo apt install python3-tk xvfb")
        print("  3. pip3 install -r requirements.txt")

        if not checks["DISPLAY"]:
            print("\n如果无法使用图形界面，可以使用命令行版本:")
            print("  python3 http_client_cli.py")
            print("\n或使用虚拟显示器:")
            print("  xvfb-run python3 http_client_enhanced.py")

    print()
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
