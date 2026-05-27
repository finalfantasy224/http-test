#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test complex curl command parsing"""

import sys
sys.path.insert(0, '.')

from core import curl_parser

# Test case: the complex curl from the user
curl_complex = """curl 'https://testlogistics.sm-os.com/api/wms-web/class/list.do?pageSize=10&curPage=1&whId=201&_=1777513725074' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: text/plain' \
  -H 'Cookie: experimentation_subject_id=ImNhZWUzODkyLTEzNDEtNGE5Yi1hMjJhLWI2OTk4MTg0ZmY0MyI%3D--a947deb65; login_user_name=%E5%AE%89%E5%BA%B7; login_token=Bearer%20eyJ0eXAiOiJKV1Q' \
  -H 'Referer: https://testlogistics.sm-os.com/frontend/wms.html'"""

print("Test: Complex curl with many headers")
print("=" * 60)
try:
    result = curl_parser.parse_curl_command(curl_complex)
    print(f"Method: {result['method']}")
    print(f"URL: {result['url']}")
    print(f"Headers count: {len(result['headers'])}")
    for k, v in result['headers'].items():
        if len(v) > 50:
            print(f"  {k}: {v[:50]}...")
        else:
            print(f"  {k}: {v}")
    print("\n✓ PASS")
except Exception as e:
    print(f"\n✗ FAIL: {e}")
    import traceback
    traceback.print_exc()

# Test case 2: Single line still works
print("\n" + "=" * 60)
print("Test: Single line curl (regression test)")
curl_simple = """curl 'https://example.com/api' -H 'Content-Type: application/json' -d '{}'"""
try:
    result = curl_parser.parse_curl_command(curl_simple)
    print(f"Method: {result['method']}")
    print(f"URL: {result['url']}")
    print(f"Body: {result['body']}")
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")

# Test case 3: Cookie with special characters
print("\n" + "=" * 60)
print("Test: Cookie with special chars (-b)")
curl_cookie = """curl -b 'session=abc123; token=xyz%40test' 'https://example.com/api'"""
try:
    result = curl_parser.parse_curl_command(curl_cookie)
    print(f"Cookie header: {result['headers'].get('Cookie', 'NOT FOUND')}")
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")