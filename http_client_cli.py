#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP客户端 - 命令行版本
适用于无GUI环境的Linux服务器
"""

import sys
import requests
import json
import argparse
from datetime import datetime

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def send_request(method, url, headers=None, data=None, timeout=30, verify=True):
    """发送HTTP请求并显示响应"""
    try:
        start_time = datetime.now()

        # 准备请求参数
        kwargs = {
            'timeout': timeout,
            'verify': verify,
        }

        if headers:
            kwargs['headers'] = headers
        if data and method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            kwargs['data'] = data

        # 发送请求
        if method == 'GET':
            response = requests.get(url, **kwargs)
        elif method == 'POST':
            response = requests.post(url, **kwargs)
        elif method == 'PUT':
            response = requests.put(url, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, **kwargs)
        elif method == 'PATCH':
            response = requests.patch(url, **kwargs)
        elif method == 'HEAD':
            response = requests.head(url, **kwargs)
        elif method == 'OPTIONS':
            response = requests.options(url, **kwargs)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # 显示响应
        print_response(response, elapsed)

    except requests.exceptions.Timeout:
        print(f"\n❌ 错误: 请求超时（{timeout}秒）")
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 连接失败，请检查URL或网络连接")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

def print_response(response, elapsed_time):
    """显示响应内容"""
    # 状态行
    print("┌────────────────────────────────────────────────────────────┐")
    print(f"│  响应状态: {response.status_code} {response.reason:<40}│")
    print(f"│  响应时间: {elapsed_time:.3f}秒{'':<40}│")

    # 计算响应大小
    content_length = len(response.content)
    if content_length < 1024:
        size_text = f"{content_length} B"
    elif content_length < 1024 * 1024:
        size_text = f"{content_length/1024:.2f} KB"
    else:
        size_text = f"{content_length/(1024*1024):.2f} MB"

    print(f"│  响应大小: {size_text:<46}│")
    print("└────────────────────────────────────────────────────────────┘")

    # 响应Headers
    print("\n┌─ 响应 Headers ─────────────────────────────────────────┐")
    for key, value in response.headers.items():
        print(f"│ {key}: {value}")
    print("└────────────────────────────────────────────────────────────┘")

    # 响应Body
    print("\n┌─ 响应 Body ─────────────────────────────────────────────┐")
    try:
        # 尝试JSON格式化
        response_json = response.json()
        formatted_json = json.dumps(response_json, indent=2, ensure_ascii=False)
        print(formatted_json)
    except (json.JSONDecodeError, ValueError):
        # 如果不是JSON，显示原始文本
        print(response.text)

    if response.text:
        print("\n" + "─"*60)

def parse_headers(header_list):
    """解析headers参数"""
    headers = {}
    for header in header_list:
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    return headers

def main():
    parser = argparse.ArgumentParser(
        description='HTTP客户端 - 命令行版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # GET请求
  %(prog)s -m GET https://httpbin.org/get

  # POST请求（JSON）
  %(prog)s -m POST https://httpbin.org/post \\
    -H "Content-Type: application/json" \\
    -d '{"name": "测试", "age": 25}'

  # 带自定义Header的GET请求
  %(prog)s -m GET https://httpbin.org/get \\
    -H "User-Agent: MyApp/1.0"

  # PUT请求
  %(prog)s -m PUT https://httpbin.org/put \\
    -H "Content-Type: application/json" \\
    -d '{"id": 123, "name": "更新"}'

  # DELETE请求
  %(prog)s -m DELETE https://httpbin.org/delete

  # 不验证SSL证书
  %(prog)s -m GET https://example.com --no-verify

  # 设置超时
  %(prog)s -m GET https://httpbin.org/delay/2 -t 5
        """
    )

    parser.add_argument('url', help='请求URL')
    parser.add_argument('-m', '--method', default='GET',
                       choices=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'],
                       help='HTTP方法（默认: GET）')
    parser.add_argument('-H', '--headers', action='append',
                       help='HTTP请求头（格式: Key: Value）')
    parser.add_argument('-d', '--data',
                       help='请求体数据')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='超时时间，秒（默认: 30）')
    parser.add_argument('--no-verify', action='store_true',
                       help='不验证SSL证书（仅用于测试）')
    parser.add_argument('--json-file', metavar='FILE',
                       help='从文件加载JSON数据作为请求体')

    args = parser.parse_args()

    # 解析URL
    url = args.url
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url

    # 解析headers
    headers = {}
    if args.headers:
        headers = parse_headers(args.headers)

    # 解析data
    data = args.data
    if args.json_file:
        try:
            with open(args.json_file, 'r', encoding='utf-8') as f:
                data = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            sys.exit(1)

    # 显示请求信息
    print_header("HTTP客户端 - 命令行版本")
    print(f"请求方法: {args.method}")
    print(f"请求URL:  {url}")
    if headers:
        print(f"请求头:   {len(headers)}个")
    if data:
        data_preview = data[:50] + '...' if len(data) > 50 else data
        print(f"请求数据: {data_preview}")
    print(f"超时时间: {args.timeout}秒")
    print(f"SSL验证:  {'开启' if not args.no_verify else '关闭'}")

    # 发送请求
    send_request(
        method=args.method,
        url=url,
        headers=headers if headers else None,
        data=data,
        timeout=args.timeout,
        verify=not args.no_verify
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
