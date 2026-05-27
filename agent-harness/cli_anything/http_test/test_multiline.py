#!/usr/bin/env python3
# Test curl multi-line parsing

import sys
sys.path.insert(0, '.')

from core import curl_parser

# Test case 1: multi-line with backslash continuation
curl1 = """curl 'https://testlogistics.sm-os.com/api/wms-web/class/list.do?pageSize=10&curPage=1&whId=201&_=1777513725074' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8'"""

print("Test 1: Multi-line curl with backslash")
print("=" * 50)
try:
    result = curl_parser.parse_curl_command(curl1)
    print(f"Method: {result['method']}")
    print(f"URL: {result['url']}")
    print(f"Headers: {result['headers']}")
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")

print()

# Test case 2: single line (should still work)
curl2 = """curl 'https://example.com/api' -H 'Content-Type: application/json' -d '{}'"""

print("Test 2: Single line curl")
print("=" * 50)
try:
    result = curl_parser.parse_curl_command(curl2)
    print(f"Method: {result['method']}")
    print(f"URL: {result['url']}")
    print(f"Body: {result['body']}")
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")