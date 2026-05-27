#!/usr/bin/env python3
# Quick test of REPL workflow commands
import sys
import io

test_input = """help
wf create "测试工作流" -c 测试
wf list
exit
"""

sys.stdin = io.StringIO(test_input)
sys.path.insert(0, '.')

from http_test_cli import repl

try:
    repl()
    print("SUCCESS")
except Exception as e:
    print(f"Error: {e}")