#!/usr/bin/env python3
# Test simplified REPL workflow commands
import sys
import io

# Test workflow commands in REPL
test_input = """wf create "仓储流程" -c 工作
wf list
wf add 1 -u https://httpbin.org/get -e json.token
wf add 1 -u https://httpbin.org/headers -m GET
wf show 1
exit
"""

sys.stdin = io.StringIO(test_input)
sys.path.insert(0, '.')

from http_test_cli import repl

print("Testing REPL workflow commands...")
print("=" * 50)
try:
    repl()
    print("=" * 50)
    print("SUCCESS")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()