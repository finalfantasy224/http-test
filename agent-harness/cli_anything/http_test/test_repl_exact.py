#!/usr/bin/env python3
# Test REPL with complex curl in multi-line input
import sys
import io

# Multi-line input with the exact curl pattern
test_input = """curl 'https://testlogistics.sm-os.com/api/wms-web/class/list.do?pageSize=10&curPage=1&whId=201' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: text/plain' \
  -H 'User-Agent: Mozilla/5.0'
exit
"""

sys.stdin = io.StringIO(test_input)
sys.path.insert(0, '.')

from http_test_cli import repl

print("Testing REPL with complex multi-line curl...")
print("-" * 50)
try:
    repl()
    print("-" * 50)
    print("REPL completed successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()