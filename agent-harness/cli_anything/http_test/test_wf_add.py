#!/usr/bin/env python3
# Test REPL workflow add
import sys
import io

test_input = """wf add 3 -u https://httpbin.org/get -m GET
wf add 3 -u https://httpbin.org/post -m POST -d test=1
wf show 3
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