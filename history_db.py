#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
历史记录数据库管理模块
使用SQLite存储HTTP请求历史记录
"""

import sqlite3
import json
import os
from datetime import datetime

class HistoryDB:
    def __init__(self, db_path="http_requests_history.db"):
        """初始化数据库"""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """创建数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建请求历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT '默认分类',
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                body TEXT,
                response_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#3498db',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 插入默认分类
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', ('默认分类',))
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', ('工作',))
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', ('测试',))
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', ('开发',))

        conn.commit()
        conn.close()

    def save_request(self, name, category, method, url, headers, body, response_info=None):
        """保存请求到历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 转换headers为JSON字符串
        headers_json = json.dumps(headers) if headers else None

        cursor.execute('''
            INSERT INTO requests (name, category, method, url, headers, body, response_info, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, method, url, headers_json, body, response_info, datetime.now()))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id

    def get_all_requests(self, category=None):
        """获取所有请求记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT id, name, category, method, url, created_at
                FROM requests
                WHERE category = ?
                ORDER BY updated_at DESC
            ''', (category,))
        else:
            cursor.execute('''
                SELECT id, name, category, method, url, created_at
                FROM requests
                ORDER BY updated_at DESC
            ''')

        results = cursor.fetchall()
        conn.close()

        # 转换为字典列表
        return [
            {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'method': row[3],
                'url': row[4],
                'created_at': row[5]
            }
            for row in results
        ]

    def get_request_by_id(self, request_id):
        """根据ID获取请求详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, category, method, url, headers, body, response_info
            FROM requests
            WHERE id = ?
        ''', (request_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            headers = json.loads(row[4]) if row[4] else {}
            return {
                'name': row[0],
                'category': row[1],
                'method': row[2],
                'url': row[3],
                'headers': headers,
                'body': row[5] or '',
                'response_info': row[6]
            }
        return None

    def delete_request(self, request_id):
        """删除请求记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM requests WHERE id = ?', (request_id,))

        conn.commit()
        conn.close()

    def get_categories(self):
        """获取所有分类"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name FROM categories ORDER BY name')
        results = cursor.fetchall()
        conn.close()

        return [{'id': row[0], 'name': row[1]} for row in results]

    def add_category(self, name):
        """添加新分类"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            conn.commit()
            category_id = cursor.lastrowid
            conn.close()
            return category_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def search_requests(self, keyword):
        """搜索请求记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, category, method, url, created_at
            FROM requests
            WHERE name LIKE ? OR url LIKE ?
            ORDER BY updated_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%'))

        results = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'method': row[3],
                'url': row[4],
                'created_at': row[5]
            }
            for row in results
        ]

    def update_request(self, request_id, name, category, method, url, headers, body):
        """更新请求记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        headers_json = json.dumps(headers) if headers else None

        cursor.execute('''
            UPDATE requests
            SET name = ?, category = ?, method = ?, url = ?, headers = ?, body = ?, updated_at = ?
            WHERE id = ?
        ''', (name, category, method, url, headers_json, body, datetime.now(), request_id))

        conn.commit()
        conn.close()

    def export_requests(self, file_path):
        """导出请求记录到文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, category, method, url, headers, body, response_info, created_at
            FROM requests
            ORDER BY created_at DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        # 转换为JSON格式
        requests_data = []
        for row in results:
            headers = json.loads(row[5]) if row[5] else {}
            requests_data.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'method': row[3],
                'url': row[4],
                'headers': headers,
                'body': row[6] or '',
                'response_info': row[7],
                'created_at': row[8]
            })

        # 保存为JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(requests_data, f, ensure_ascii=False, indent=2)

        return len(requests_data)

    def import_requests(self, file_path):
        """从文件导入请求记录"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                requests_data = json.load(f)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            imported_count = 0
            for req_data in requests_data:
                headers_json = json.dumps(req_data.get('headers', {}))
                cursor.execute('''
                    INSERT INTO requests (name, category, method, url, headers, body, response_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    req_data.get('name', '导入请求'),
                    req_data.get('category', '导入'),
                    req_data.get('method', 'GET'),
                    req_data.get('url', ''),
                    headers_json,
                    req_data.get('body', ''),
                    req_data.get('response_info')
                ))
                imported_count += 1

            conn.commit()
            conn.close()
            return imported_count
        except Exception as e:
            print(f"导入失败: {e}")
            return 0
