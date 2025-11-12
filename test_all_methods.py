#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面测试HTTP客户端的所有功能
"""

import sys
import requests
import json
from datetime import datetime

class HTTPTester:
    def __init__(self):
        self.success_count = 0
        self.fail_count = 0
        self.results = []

    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}")

    def print_result(self, method, url, success, status_code="", elapsed="", error=""):
        """打印测试结果"""
        if success:
            print(f"✅ {method:6} | {status_code:3} | {elapsed:8} | {url}")
            self.success_count += 1
            self.results.append((method, url, success, status_code))
        else:
            print(f"❌ {method:6} | ERROR: {error}")
            self.fail_count += 1
            self.results.append((method, url, success, "", error))

    def test_get(self):
        """测试GET请求"""
        self.print_header("1. 测试GET请求")

        try:
            start = datetime.now()
            response = requests.get('https://httpbin.org/get', timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("GET", "https://httpbin.org/get", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("GET", "https://httpbin.org/get", False, error="Unexpected status")
        except Exception as e:
            self.print_result("GET", "https://httpbin.org/get", False, error=str(e))

    def test_post_json(self):
        """测试POST请求（JSON）"""
        self.print_header("2. 测试POST请求（JSON）")

        try:
            data = {"name": "测试用户", "email": "test@example.com"}
            headers = {"Content-Type": "application/json"}

            start = datetime.now()
            response = requests.post('https://httpbin.org/post',
                                   json=data, headers=headers, timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("POST", "https://httpbin.org/post", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("POST", "https://httpbin.org/post", False, error="Unexpected status")
        except Exception as e:
            self.print_result("POST", "https://httpbin.org/post", False, error=str(e))

    def test_put(self):
        """测试PUT请求"""
        self.print_header("3. 测试PUT请求")

        try:
            data = {"id": 123, "status": "updated"}
            headers = {"Content-Type": "application/json"}

            start = datetime.now()
            response = requests.put('https://httpbin.org/put',
                                  json=data, headers=headers, timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("PUT", "https://httpbin.org/put", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("PUT", "https://httpbin.org/put", False, error="Unexpected status")
        except Exception as e:
            self.print_result("PUT", "https://httpbin.org/put", False, error=str(e))

    def test_delete(self):
        """测试DELETE请求"""
        self.print_header("4. 测试DELETE请求")

        try:
            start = datetime.now()
            response = requests.delete('https://httpbin.org/delete', timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("DELETE", "https://httpbin.org/delete", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("DELETE", "https://httpbin.org/delete", False, error="Unexpected status")
        except Exception as e:
            self.print_result("DELETE", "https://httpbin.org/delete", False, error=str(e))

    def test_patch(self):
        """测试PATCH请求"""
        self.print_header("5. 测试PATCH请求")

        try:
            data = {"field": "new_value"}
            headers = {"Content-Type": "application/json"}

            start = datetime.now()
            response = requests.patch('https://httpbin.org/patch',
                                    json=data, headers=headers, timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("PATCH", "https://httpbin.org/patch", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("PATCH", "https://httpbin.org/patch", False, error="Unexpected status")
        except Exception as e:
            self.print_result("PATCH", "https://httpbin.org/patch", False, error=str(e))

    def test_head(self):
        """测试HEAD请求"""
        self.print_header("6. 测试HEAD请求")

        try:
            start = datetime.now()
            response = requests.head('https://httpbin.org/get', timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("HEAD", "https://httpbin.org/get", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("HEAD", "https://httpbin.org/get", False, error="Unexpected status")
        except Exception as e:
            self.print_result("HEAD", "https://httpbin.org/get", False, error=str(e))

    def test_options(self):
        """测试OPTIONS请求"""
        self.print_header("7. 测试OPTIONS请求")

        try:
            start = datetime.now()
            response = requests.options('https://httpbin.org/get', timeout=10)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                self.print_result("OPTIONS", "https://httpbin.org/get", True,
                                str(response.status_code), f"{elapsed:.3f}s")
            else:
                self.print_result("OPTIONS", "https://httpbin.org/get", False, error="Unexpected status")
        except Exception as e:
            self.print_result("OPTIONS", "https://httpbin.org/get", False, error=str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("  HTTP客户端 - 全面功能测试")
        print("="*60)

        # 运行所有测试
        self.test_get()
        self.test_post_json()
        self.test_put()
        self.test_delete()
        self.test_patch()
        self.test_head()
        self.test_options()

        # 显示总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")

        total = self.success_count + self.fail_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        print(f"总测试数: {total}")
        print(f"成功: {self.success_count}")
        print(f"失败: {self.fail_count}")
        print(f"成功率: {success_rate:.1f}%")

        if self.fail_count == 0:
            print("\n🎉 所有测试通过！HTTP客户端工作正常！")
        else:
            print(f"\n⚠️  有 {self.fail_count} 个测试失败")
            print("\n失败的测试:")
            for method, url, success, status, error in self.results:
                if not success:
                    print(f"  - {method} {url}: {error}")

        print("\n" + "="*60)

if __name__ == "__main__":
    tester = HTTPTester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
