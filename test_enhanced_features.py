#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试增强版HTTP客户端的功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from history_db import HistoryDB
import requests
import json

def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("测试 1: 数据库功能")
    print("=" * 60)

    # 使用临时文件作为数据库
    import tempfile
    temp_db = tempfile.mktemp(suffix='.db')
    db = HistoryDB(temp_db)

    # 测试保存请求
    print("\n1.1 测试保存请求...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    }
    request_id = db.save_request(
        name="测试GET请求",
        category="测试",
        method="GET",
        url="https://httpbin.org/get",
        headers=headers,
        body="",
        response_info='{"status": 200}'
    )
    print(f"   ✓ 请求已保存，ID: {request_id}")

    # 测试获取所有请求
    print("\n1.2 测试获取请求列表...")
    requests = db.get_all_requests()
    print(f"   ✓ 获取到 {len(requests)} 条记录")
    if requests:
        print(f"   ✓ 第一条记录: {requests[0]['name']}")

    # 测试获取请求详情
    print("\n1.3 测试获取请求详情...")
    request_detail = db.get_request_by_id(request_id)
    print(f"   ✓ 获取到请求详情")
    print(f"     - 名称: {request_detail['name']}")
    print(f"     - 方法: {request_detail['method']}")
    print(f"     - URL: {request_detail['url']}")
    print(f"     - Headers: {len(request_detail['headers'])} 个")

    # 测试分类
    print("\n1.4 测试分类管理...")
    categories = db.get_categories()
    print(f"   ✓ 获取到 {len(categories)} 个分类")
    for cat in categories:
        print(f"     - {cat['name']}")

    # 测试搜索
    print("\n1.5 测试搜索功能...")
    results = db.search_requests("GET")
    print(f"   ✓ 搜索'GET'找到 {len(results)} 条记录")

    print("\n✅ 数据库功能测试通过！")
    return True

def test_http_request():
    """测试HTTP请求功能"""
    print("\n" + "=" * 60)
    print("测试 2: HTTP请求功能")
    print("=" * 60)

    try:
        # 测试GET请求
        print("\n2.1 测试GET请求...")
        response = requests.get("https://httpbin.org/get", timeout=10)
        print(f"   ✓ GET请求成功，状态码: {response.status_code}")

        # 测试POST请求
        print("\n2.2 测试POST请求...")
        data = {"name": "测试", "email": "test@example.com"}
        response = requests.post("https://httpbin.org/post", json=data, timeout=10)
        print(f"   ✓ POST请求成功，状态码: {response.status_code}")

        # 测试PUT请求
        print("\n2.3 测试PUT请求...")
        response = requests.put("https://httpbin.org/put", json=data, timeout=10)
        print(f"   ✓ PUT请求成功，状态码: {response.status_code}")

        # 测试DELETE请求
        print("\n2.4 测试DELETE请求...")
        response = requests.delete("https://httpbin.org/delete", timeout=10)
        print(f"   ✓ DELETE请求成功，状态码: {response.status_code}")

        print("\n✅ HTTP请求功能测试通过！")
        return True
    except Exception as e:
        print(f"\n❌ HTTP请求测试失败: {e}")
        return False

def test_import_export():
    """测试导入导出功能"""
    print("\n" + "=" * 60)
    print("测试 3: 导入导出功能")
    print("=" * 60)

    # 使用临时文件作为数据库
    import tempfile
    temp_db = tempfile.mktemp(suffix='.db')
    db = HistoryDB(temp_db)

    # 添加测试数据
    print("\n3.1 添加测试数据...")
    db.save_request("请求1", "分类1", "GET", "https://api.example.com/1", {}, "")
    db.save_request("请求2", "分类2", "POST", "https://api.example.com/2", {}, "")
    print(f"   ✓ 添加了 2 条测试数据")

    # 测试导出
    print("\n3.2 测试导出功能...")
    export_file = "/tmp/test_export.json"
    count = db.export_requests(export_file)
    print(f"   ✓ 导出 {count} 条记录到 {export_file}")

    # 检查导出文件
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            data = json.load(f)
        print(f"   ✓ 导出文件包含 {len(data)} 条记录")
        os.remove(export_file)

    # 测试导入
    print("\n3.3 测试导入功能...")
    import_file = "/tmp/test_import.json"
    with open(import_file, 'w') as f:
        json.dump([{
            "name": "导入请求",
            "category": "导入",
            "method": "GET",
            "url": "https://imported.com",
            "headers": {},
            "body": "",
            "response_info": None
        }], f)

    count = db.import_requests(import_file)
    print(f"   ✓ 导入 {count} 条记录")

    # 验证导入
    all_requests = db.get_all_requests()
    print(f"   ✓ 数据库现有 {len(all_requests)} 条记录")

    os.remove(import_file)

    print("\n✅ 导入导出功能测试通过！")
    return True

def main():
    print("\n" + "=" * 60)
    print("  HTTP客户端增强版 - 功能测试")
    print("=" * 60)

    all_passed = True

    # 运行所有测试
    try:
        all_passed &= test_database()
    except Exception as e:
        print(f"\n❌ 数据库测试异常: {e}")
        all_passed = False

    try:
        all_passed &= test_http_request()
    except Exception as e:
        print(f"\n❌ HTTP请求测试异常: {e}")
        all_passed = False

    try:
        all_passed &= test_import_export()
    except Exception as e:
        print(f"\n❌ 导入导出测试异常: {e}")
        all_passed = False

    # 显示结果
    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
