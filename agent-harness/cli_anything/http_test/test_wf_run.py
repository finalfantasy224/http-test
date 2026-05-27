#!/usr/bin/env python3
# Test REPL workflow run
import sys
import io

test_input = """wf run 3
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