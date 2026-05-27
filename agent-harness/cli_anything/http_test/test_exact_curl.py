#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test EXACT curl from user's example"""

import sys
sys.path.insert(0, '.')

from core import curl_parser

# EXACT curl from user's example - just truncated for safety
curl_exact = """curl 'https://testlogistics.sm-os.com/api/wms-web/class/list.do?pageSize=10&curPage=1&whId=201&_=1777513725074' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: text/plain' \
  -b 'experimentation_subject_id=ImNhZWUzODkyLTEzNDEtNGE5Yi1hMjJhLWI2OTk4MTg0ZmY0MyI%3D--a947deb6528bf2cc8d4c3c263058b48cd20db12c; login_user_name=%E5%AE%89%E5%BA%B7; login_type=vpn; loginType=undefined; login_dmall_id=kang.an; logistics-emq-id=emq-39ef8b01-9; logistics-time-zone-id=+08:00; _ga=GA1.1.1840843603.1774927498; _ga_0C4M1PWYZ7=GS2.1.s1774927497$o1$g0$t1774927498$j59$l0$h0; _ga_T11SF3WXX2=GS2.1.s1774927498$o1$g0$t1774927498$j60$l0$h0; _ga_K2SPJK2C73=GS2.1.s1774927498$o1$g0$t1774927498$j60$l0$h0; logistics-lang=zh_CN; guardian_id=Yb3BHSVbHS8Vk8rIIS8VrhMLF2v0Q/sCIB+jQBf/96M=; login_token=Bearer%20eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3Nzc0NDg2OTc2NjksImV4cCI6MTc3ODA1MzQ5NzY2OSwiaXNzIjoia2VuIiwiZGF0YSI6eyJ1c2VyX2luZm8iOnsidXNlcl9pZCI6MzgyOTcyMSwidXNlcl9jb2RlIjoia2FuZy5hbiIsInVzZXJfbmFtZSI6Ilx1NWI4OVx1NWViNyIsInByZWZlcnJlZF9uYW1lIjoiXHU1Yjg5XHU1ZWI3IiwicGhvbmUiOiIiLCJlbWFpbCI6ImthbmcuYW5AZG1hbGwuY29tIiwiaHJzX2lkIjo0MDI0ODAxLCJocm1zX2lkIjoxMDAwMDg2NDQxLCJ1c2VyX25vIjoiMDA2NDI5MjAifSwibG9naW5fdGltZSI6MTc3NzQ0ODY5NzY2OX19.aljcEgNngCqXyPMBrwpOxJ19_N4vz9b4WOz44T337L0; return_url=https://rdms.dmall.com/#index/portal/portal/workload; logistics-session-token=b687ec81443611f1b262838b74fdca75; logistics-merchant=f90e4732e4d7a4581e9f1ddd676411bd; logistics-merchant-code=SM; guardian_id=uiKTgOy94BW41FSVVgKsSTx9+mXQOV44mfHSalg73T8=; messageId=wms_MP_vtn0mb_5f5e106' \
  -H 'Referer: https://testlogistics.sm-os.com/front/wms/configuration/warehouseconfig/warehousetypes/list.html?pageSize=10&curPage=1&whId=201' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"'"""

print("=" * 60)
print("Parsing EXACT curl from user:")
print("=" * 60)

try:
    result = curl_parser.parse_curl_command(curl_exact)
    print(f"Method: {result['method']}")
    print(f"URL: {result['url']}")
    print(f"\nHeaders ({len(result['headers'])}):")
    for k, v in result['headers'].items():
        if len(v) > 60:
            print(f"  {k}: {v[:60]}...")
        else:
            print(f"  {k}: {v}")
    print("\n✓ SUCCESS")
except Exception as e:
    print(f"\n✗ FAILED: {e}")
    import traceback
    traceback.print_exc()