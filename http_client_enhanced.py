#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import ssl
import socket
import re
import base64
from datetime import datetime
from history_db import HistoryDB

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)


def tokenize_curl(s):
    """将 curl 命令字符串按 shell 规则拆分为 token，尊重单引号、双引号。"""
    # 行尾反斜杠续行：去掉 \ 与后续换行
    s = re.sub(r'\\\s*\n', '\n', s)
    s = re.sub(r'\\\s*\r\n', '\n', s)
    tokens = []
    i = 0
    n = len(s)
    current = []

    while i < n:
        c = s[i]
        if c in ' \t\n\r':
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            continue
        if c == "'":
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            while i < n and s[i] != "'":
                if s[i] == '\\':
                    i += 1
                    if i < n:
                        current.append(s[i])
                    i += 1
                else:
                    current.append(s[i])
                    i += 1
            if i < n:
                i += 1  # skip closing '
            tokens.append(''.join(current))
            current = []
            continue
        if c == '"':
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            while i < n and s[i] != '"':
                if s[i] == '\\':
                    i += 1
                    if i < n:
                        current.append(s[i])
                    i += 1
                else:
                    current.append(s[i])
                    i += 1
            if i < n:
                i += 1
            tokens.append(''.join(current))
            current = []
            continue
        current.append(c)
        i += 1

    if current:
        tokens.append(''.join(current))
    return tokens


def parse_curl_command(curl_str):
    """
    解析 curl 命令字符串，返回请求参数字典。
    返回: dict 包含 method, url, headers, body；解析失败抛出 ValueError。
    """
    curl_str = curl_str.strip()
    if not curl_str.lower().startswith('curl'):
        raise ValueError("不是有效的 curl 命令（应以 curl 开头）")

    tokens = tokenize_curl(curl_str)
    if not tokens:
        raise ValueError("无法解析 curl 命令")

    # 去掉开头的 "curl"
    if tokens[0].lower() == 'curl':
        tokens = tokens[1:]

    method = "GET"
    url = None
    headers = {}
    body = None
    body_parts = []
    i = 0

    while i < len(tokens):
        t = tokens[i]
        t_lower = t.lower()

        if t in ('-X', '--request'):
            i += 1
            if i < len(tokens):
                method = tokens[i].upper()
            i += 1
            continue

        if t in ('-H', '--header'):
            i += 1
            if i < len(tokens):
                h = tokens[i]
                if ':' in h:
                    k, _, v = h.partition(':')
                    headers[k.strip()] = v.strip()
            i += 1
            continue

        if t_lower in ('-d', '--data', '--data-raw', '--data-ascii'):
            i += 1
            if i < len(tokens):
                body_parts.append(tokens[i])
            i += 1
            continue

        if t_lower == '--data-binary':
            i += 1
            if i < len(tokens):
                body_parts.append(tokens[i])
            i += 1
            continue

        if t in ('-u', '--user'):
            i += 1
            if i < len(tokens):
                user_pass = tokens[i]
                if ':' in user_pass:
                    up = user_pass.split(':', 1)
                    raw = (up[0] + ':' + up[1]).encode('utf-8')
                    headers['Authorization'] = 'Basic ' + base64.b64encode(raw).decode('ascii')
                else:
                    raw = (user_pass + ':').encode('utf-8')
                    headers['Authorization'] = 'Basic ' + base64.b64encode(raw).decode('ascii')
            i += 1
            continue

        if t in ('-b', '--cookie'):
            i += 1
            if i < len(tokens):
                headers['Cookie'] = tokens[i]
            i += 1
            continue

        if t_lower == '--url':
            i += 1
            if i < len(tokens):
                url = tokens[i]
            i += 1
            continue

        if t_lower in ('-g', '--get'):
            method = 'GET'
            i += 1
            continue

        # 未加 -X 时，有 -d/--data 通常表示 POST
        if t.startswith('http://') or t.startswith('https://'):
            if url is None:
                url = t
            i += 1
            continue

        i += 1

    if body_parts and method == 'GET':
        method = 'POST'
    if body_parts:
        body = '\n'.join(body_parts)

    if url is None:
        raise ValueError("curl 命令中未找到 URL")

    return {
        'method': method,
        'url': url,
        'headers': headers,
        'body': body or ''
    }

class ClosableNotebook(ttk.Frame):
    """可关闭标签页的Notebook控件"""

    def __init__(self, parent, on_close_tab=None, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True)
        self._on_close_tab = on_close_tab
        self._tabs = {}  # 存储标签页ID到实例的映射

        # 绑定标签页变化事件
        self._notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

    def add(self, child, **kwargs):
        """添加标签页"""
        # 获取标签页文本
        text = kwargs.get('text', '标签页')

        # 创建标签页
        self._notebook.add(child, **kwargs)

        # 获取新添加的标签页ID
        tab_id = self._notebook.tabs()[-1]

        # 添加关闭按钮到标签页
        self._add_close_button(tab_id, text)

        # 存储标签页实例
        self._tabs[tab_id] = child

        return child

    def _add_close_button(self, tab_id, text):
        """为标签页添加关闭按钮"""
        # 获取标签页内部框架
        notebook = self._notebook
        tab_frame = notebook.nametowidget(tab_id)

        # 清空默认内容
        for widget in tab_frame.winfo_children():
            widget.destroy()

        # 创建水平布局
        inner_frame = ttk.Frame(tab_frame)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # 标签页标题
        label = ttk.Label(inner_frame, text=text)
        label.pack(side=tk.LEFT, padx=(4, 0))

        # 关闭按钮
        close_btn = ttk.Button(
            inner_frame,
            text='×',
            width=3,
            command=lambda: self._close_tab(tab_id)
        )
        close_btn.pack(side=tk.RIGHT)

        # 鼠标悬停效果
        def on_enter(e):
            close_btn.configure(style='Hover.TButton')

        def on_leave(e):
            close_btn.configure(style='TButton')

        close_btn.bind('<Enter>', on_enter)
        close_btn.bind('<Leave>', on_leave)

        # 存储引用以便后续删除
        close_btn._tab_id = tab_id

    def _close_tab(self, tab_id):
        """关闭标签页"""
        # 获取对应的框架
        tab_frame = self._notebook.nametowidget(tab_id)

        # 检查是否是最后一个标签页
        if len(self._notebook.tabs()) <= 1:
            messagebox.showwarning("警告", "不能关闭最后一个标签页")
            return

        # 调用回调函数
        if self._on_close_tab:
            self._on_close_tab(tab_id, tab_frame)

        # 从映射中删除
        if tab_id in self._tabs:
            del self._tabs[tab_id]

        # 关闭标签页
        self._notebook.forget(tab_id)

    def _on_tab_changed(self, event):
        """标签页变化事件"""
        pass

    def select(self, tab_id=None):
        """选择标签页"""
        if tab_id:
            self._notebook.select(tab_id)
        else:
            return self._notebook.select()

    def tabs(self):
        """获取所有标签页ID"""
        return self._notebook.tabs()

    def forget(self, tab_id):
        """忘记标签页"""
        if tab_id in self._tabs:
            del self._tabs[tab_id]
        self._notebook.forget(tab_id)

    def nametowidget(self, name):
        """获取标签页组件"""
        return self._notebook.nametowidget(name)

    def set_tab_text(self, tab_id, text):
        """更新标签页标题文字"""
        tab_frame = self._notebook.nametowidget(tab_id)
        for w in tab_frame.winfo_children():
            if isinstance(w, ttk.Frame):
                for c in w.winfo_children():
                    if isinstance(c, ttk.Label):
                        c.configure(text=text)
                        return

class RequestTab:
    """单个请求标签页类"""

    def __init__(self, parent_notebook, db, name="新请求"):
        self.db = db
        self.parent = parent_notebook
        self.response_data = None

        # 创建标签页内容
        self.frame = ttk.Frame(parent_notebook, padding="10")
        self.parent.add(self.frame, text=name)

        # 初始化UI
        self.create_widgets()

    def create_widgets(self):
        """创建标签页内容"""
        self.create_request_section()
        self.create_response_section()

    def create_request_section(self):
        """创建请求区域"""
        # 请求头部框架
        req_frame = ttk.LabelFrame(self.frame, text="请求设置", padding="10")
        req_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：方法、URL、发送按钮
        row1 = ttk.Frame(req_frame)
        row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row1, text="方法:").pack(side=tk.LEFT)
        self.method_var = tk.StringVar(value="GET")
        method_combo = ttk.Combobox(row1, textvariable=self.method_var,
                                    values=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                                    state="readonly", width=10)
        method_combo.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(row1, text="URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(row1, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))

        self.send_button = ttk.Button(row1, text="发送请求 (Ctrl+Enter)", command=self.send_request)
        self.send_button.pack(side=tk.RIGHT)

        # 第二行：高级设置
        row2 = ttk.Frame(req_frame)
        row2.pack(fill=tk.X)

        ttk.Label(row2, text="超时:").pack(side=tk.LEFT)
        self.timeout_var = tk.StringVar(value="30")
        ttk.Entry(row2, textvariable=self.timeout_var, width=10).pack(side=tk.LEFT, padx=(5, 10))

        self.verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="验证SSL", variable=self.verify_var).pack(side=tk.LEFT, padx=(0, 20))

        # 保存和加载按钮
        ttk.Button(row2, text="保存请求", command=self.save_request).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row2, text="清空", command=self.clear_all).pack(side=tk.LEFT)

        # 标签页：Headers和Body
        self.notebook = ttk.Notebook(req_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Headers标签页
        headers_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(headers_frame, text="Headers")

        headers_tree_frame = ttk.Frame(headers_frame)
        headers_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.headers_tree = ttk.Treeview(headers_tree_frame, columns=("key", "value"), show="tree headings", height=6)
        self.headers_tree.heading("#0", text="#")
        self.headers_tree.heading("key", text="Header Name")
        self.headers_tree.heading("value", text="Header Value")
        self.headers_tree.column("#0", width=50)
        self.headers_tree.column("key", width=200)
        self.headers_tree.column("value", width=400)
        self.headers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        headers_scroll = ttk.Scrollbar(headers_tree_frame, orient=tk.VERTICAL, command=self.headers_tree.yview)
        headers_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.headers_tree.configure(yscrollcommand=headers_scroll.set)

        # 绑定双击编辑事件
        self.headers_tree.bind('<Double-1>', self.on_header_double_click)
        self.headers_edit_entry = None
        self.headers_edit_item = None
        self.headers_edit_column = None

        # Headers按钮
        headers_btn_frame = ttk.Frame(headers_frame)
        headers_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(headers_btn_frame, text="添加", command=self.add_header).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(headers_btn_frame, text="删除", command=self.delete_header).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(headers_btn_frame, text="清空", command=self.clear_headers).pack(side=tk.LEFT)

        # 添加默认header
        self.headers_tree.insert("", tk.END, text="1", values=("Content-Type", "application/json"))

        # Body标签页
        body_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(body_frame, text="Body")

        self.body_text = scrolledtext.ScrolledText(body_frame, height=10, wrap=tk.WORD)
        self.body_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        body_btn_frame = ttk.Frame(body_frame)
        body_btn_frame.pack(fill=tk.X)
        ttk.Button(body_btn_frame, text="清空", command=lambda: self.body_text.delete(1.0, tk.END)).pack(side=tk.LEFT)

    def create_response_section(self):
        """创建响应区域"""
        resp_frame = ttk.LabelFrame(self.frame, text="响应", padding="10")
        resp_frame.pack(fill=tk.BOTH, expand=True)

        # 响应状态
        status_frame = ttk.Frame(resp_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="未发送")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 9, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(status_frame, text="时间:").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="-")
        ttk.Label(status_frame, textvariable=self.time_var).pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(status_frame, text="大小:").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="-")
        ttk.Label(status_frame, textvariable=self.size_var).pack(side=tk.LEFT, padx=(5, 0))

        # 响应标签页
        self.resp_notebook = ttk.Notebook(resp_frame)
        self.resp_notebook.pack(fill=tk.BOTH, expand=True)

        # 响应Body
        body_resp_frame = ttk.Frame(self.resp_notebook, padding="5")
        self.resp_notebook.add(body_resp_frame, text="Body")
        self.response_text = scrolledtext.ScrolledText(body_resp_frame, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)

        # 响应Headers
        headers_resp_frame = ttk.Frame(self.resp_notebook, padding="5")
        self.resp_notebook.add(headers_resp_frame, text="Headers")

        self.response_headers_tree = ttk.Treeview(headers_resp_frame, columns=("key", "value"), show="tree headings")
        self.response_headers_tree.heading("#0", text="#")
        self.response_headers_tree.heading("key", text="Header Name")
        self.response_headers_tree.heading("value", text="Header Value")
        self.response_headers_tree.column("#0", width=50)
        self.response_headers_tree.column("key", width=300)
        self.response_headers_tree.column("value", width=500)
        self.response_headers_tree.pack(fill=tk.BOTH, expand=True)

        resp_headers_scroll = ttk.Scrollbar(headers_resp_frame, orient=tk.VERTICAL,
                                           command=self.response_headers_tree.yview)
        resp_headers_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_headers_tree.configure(yscrollcommand=resp_headers_scroll.set)

    def on_header_double_click(self, event):
        """双击 header 单元格时开始编辑"""
        # 取消之前的编辑
        if self.headers_edit_entry:
            self.finish_header_edit()

        # 获取点击位置
        region = self.headers_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # 获取点击的行和列
        item = self.headers_tree.identify_row(event.y)
        column = self.headers_tree.identify_column(event.x)

        if not item:
            return

        # 列索引：1=key, 2=value
        if column == "#1":
            col_index = 0  # key 列
        elif column == "#2":
            col_index = 1  # value 列
        else:
            return  # 不编辑 #0 列（序号）

        # 获取当前值
        values = list(self.headers_tree.item(item, 'values'))
        current_value = values[col_index] if col_index < len(values) else ""

        # 获取单元格位置
        bbox = self.headers_tree.bbox(item, column)
        if not bbox:
            return

        x, y, width, height = bbox

        # 创建编辑 Entry（宽度使用像素值）
        self.headers_edit_entry = ttk.Entry(self.headers_tree)
        self.headers_edit_entry.place(x=x, y=y, width=width, height=height)
        self.headers_edit_entry.insert(0, current_value)
        self.headers_edit_entry.select_range(0, tk.END)
        self.headers_edit_entry.focus()

        # 保存编辑上下文
        self.headers_edit_item = item
        self.headers_edit_column = col_index

        # 绑定事件
        self.headers_edit_entry.bind('<Return>', lambda e: self.finish_header_edit())
        self.headers_edit_entry.bind('<Escape>', lambda e: self.cancel_header_edit())
        self.headers_edit_entry.bind('<FocusOut>', lambda e: self.finish_header_edit())

    def finish_header_edit(self):
        """完成 header 编辑"""
        if not self.headers_edit_entry or not self.headers_edit_item:
            return

        try:
            new_value = self.headers_edit_entry.get()
            item = self.headers_edit_item
            col_index = self.headers_edit_column

            # 检查 item 是否仍然存在
            if item not in self.headers_tree.get_children() and item != "":
                # item 已被删除，只清理编辑状态
                self.headers_edit_entry.destroy()
                self.headers_edit_entry = None
                self.headers_edit_item = None
                self.headers_edit_column = None
                return

            # 获取当前值
            values = list(self.headers_tree.item(item, 'values'))
            # 确保有足够的列
            while len(values) < 2:
                values.append("")
            # 更新对应列的值
            values[col_index] = new_value

            # 更新 Treeview
            self.headers_tree.item(item, values=tuple(values))
        except tk.TclError:
            # Entry 可能已被销毁
            pass
        finally:
            # 清理
            if self.headers_edit_entry:
                try:
                    self.headers_edit_entry.destroy()
                except:
                    pass
            self.headers_edit_entry = None
            self.headers_edit_item = None
            self.headers_edit_column = None

    def cancel_header_edit(self):
        """取消 header 编辑"""
        if self.headers_edit_entry:
            try:
                self.headers_edit_entry.destroy()
            except:
                pass
            self.headers_edit_entry = None
            self.headers_edit_item = None
            self.headers_edit_column = None

    def add_header(self):
        """添加header"""
        # 如果正在编辑，先完成编辑
        if self.headers_edit_entry:
            self.finish_header_edit()

        items = self.headers_tree.get_children()
        new_id = str(len(items) + 1)
        self.headers_tree.insert("", tk.END, text=new_id, values=("", ""))

    def delete_header(self):
        """删除header"""
        # 如果正在编辑，先完成编辑
        if self.headers_edit_entry:
            self.finish_header_edit()

        selected = self.headers_tree.selection()
        if selected:
            self.headers_tree.delete(selected)

    def clear_headers(self):
        """清空headers"""
        # 如果正在编辑，先完成编辑
        if self.headers_edit_entry:
            self.finish_header_edit()

        if messagebox.askyesno("确认", "清空所有Headers?"):
            for item in self.headers_tree.get_children():
                self.headers_tree.delete(item)
            self.add_header()

    def collect_headers(self):
        """收集headers"""
        # 如果正在编辑，先完成编辑以确保收集最新值
        if self.headers_edit_entry:
            self.finish_header_edit()

        headers = {}
        for item in self.headers_tree.get_children():
            values = self.headers_tree.item(item, 'values')
            if len(values) == 2 and values[0].strip():
                headers[values[0].strip()] = values[1].strip()
        return headers

    def save_request(self):
        """保存请求到历史记录"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "请先输入URL")
            return

        # 获取分类列表
        categories = self.db.get_categories()
        category_names = [cat['name'] for cat in categories]

        # 延迟导入SaveRequestDialog以避免类定义顺序问题
        from __main__ import SaveRequestDialog

        # 创建保存对话框
        dialog = SaveRequestDialog(self.parent, url, category_names)
        self.parent.wait_window(dialog.dialog)

        # 如果用户点击取消，则返回
        if not dialog.result:
            return

        name, category = dialog.result

        # 保存到数据库
        headers = self.collect_headers()
        body = self.body_text.get(1.0, tk.END).strip()
        method = self.method_var.get()

        try:
            self.db.save_request(name, category, method, url, headers, body)
            messagebox.showinfo("成功", f"请求已保存到分类: {category}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def clear_all(self):
        """清空所有内容"""
        if messagebox.askyesno("确认", "清空所有内容?"):
            self.url_entry.delete(0, tk.END)
            self.method_var.set("GET")
            self.clear_headers()
            self.body_text.delete(1.0, tk.END)
            self.clear_response()

    def clear_response(self):
        """清空响应"""
        self.response_text.delete(1.0, tk.END)
        for item in self.response_headers_tree.get_children():
            self.response_headers_tree.delete(item)
        self.status_var.set("未发送")
        self.time_var.set("-")
        self.size_var.set("-")

    def send_request(self):
        """发送HTTP请求"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入URL")
            return

        # 验证URL
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        method = self.method_var.get()
        headers = self.collect_headers()
        body = None

        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            body = self.body_text.get(1.0, tk.END).strip()

        try:
            timeout = int(self.timeout_var.get())
        except ValueError:
            timeout = 30

        verify_ssl = self.verify_var.get()

        # 清空之前响应
        self.clear_response()

        # 禁用发送按钮
        self.send_button.configure(state='disabled', text='发送中...')
        self.parent.master.update()

        try:
            start_time = datetime.now()

            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout, verify=verify_ssl)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=body, timeout=timeout, verify=verify_ssl)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=body, timeout=timeout, verify=verify_ssl)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout, verify=verify_ssl)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, data=body, timeout=timeout, verify=verify_ssl)
            elif method == "HEAD":
                response = requests.head(url, headers=headers, timeout=timeout, verify=verify_ssl)
            elif method == "OPTIONS":
                response = requests.options(url, headers=headers, timeout=timeout, verify=verify_ssl)
            else:
                raise ValueError(f"不支持的方法: {method}")

            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            self.display_response(response, elapsed)
            self.response_data = response

        except Exception as e:
            self.status_var.set(f"错误: {str(e)[:50]}")
            messagebox.showerror("错误", f"请求失败: {e}")
        finally:
            self.send_button.configure(state='normal', text='发送请求 (Ctrl+Enter)')

    def display_response(self, response, elapsed_time):
        """显示响应"""
        status_code = response.status_code
        status_text = f"{status_code} - {response.reason}"
        self.status_var.set(status_text)

        if 200 <= status_code < 300:
            self.status_label.configure(foreground="green")
        elif 300 <= status_code < 400:
            self.status_label.configure(foreground="orange")
        else:
            self.status_label.configure(foreground="red")

        self.time_var.set(f"{elapsed_time:.3f}s")

        content_length = len(response.content)
        if content_length < 1024:
            size_text = f"{content_length} B"
        elif content_length < 1024 * 1024:
            size_text = f"{content_length/1024:.2f} KB"
        else:
            size_text = f"{content_length/(1024*1024):.2f} MB"
        self.size_var.set(size_text)

        try:
            response_json = response.json()
            response_text = json.dumps(response_json, indent=2, ensure_ascii=False)
        except:
            response_text = response.text

        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(1.0, response_text)

        for i, (key, value) in enumerate(response.headers.items(), 1):
            self.response_headers_tree.insert("", tk.END, text=str(i), values=(key, value))

    def load_request_data(self, request_data):
        """加载请求数据"""
        # 如果正在编辑，先完成编辑
        if self.headers_edit_entry:
            self.finish_header_edit()

        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, request_data['url'])
        self.method_var.set(request_data['method'])

        # 加载headers
        for item in self.headers_tree.get_children():
            self.headers_tree.delete(item)

        headers = request_data.get('headers', {})
        for i, (key, value) in enumerate(headers.items(), 1):
            self.headers_tree.insert("", tk.END, text=str(i), values=(key, value))

        if not headers:
            self.headers_tree.insert("", tk.END, text="1", values=("Content-Type", "application/json"))

        # 加载body
        self.body_text.delete(1.0, tk.END)
        if request_data.get('body'):
            self.body_text.insert(1.0, request_data['body'])


class SaveRequestDialog:
    """保存请求的对话框"""

    def __init__(self, parent, url, category_names):
        self.result = None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("保存请求")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        # 请求名称
        ttk.Label(self.dialog, text="请求名称:").pack(pady=(20, 5))
        self.name_var = tk.StringVar(value=url)
        name_entry = ttk.Entry(self.dialog, textvariable=self.name_var, width=40)
        name_entry.pack(pady=(0, 10))
        name_entry.focus()

        # 分类选择
        ttk.Label(self.dialog, text="分类:").pack(pady=(5, 5))
        self.category_var = tk.StringVar(value=category_names[0] if category_names else "默认分类")
        category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var,
                                      values=category_names, state="readonly", width=37)
        category_combo.pack(pady=(0, 10))

        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT, padx=10)

        # 绑定快捷键
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())

    def ok_clicked(self):
        """确定按钮点击"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入请求名称")
            return

        category = self.category_var.get().strip()
        if not category:
            messagebox.showerror("错误", "请选择分类")
            return

        self.result = (name, category)
        self.dialog.destroy()

    def cancel_clicked(self):
        """取消按钮点击"""
        self.result = None
        self.dialog.destroy()


class ImportCurlDialog:
    """导入 curl 命令的对话框"""

    def __init__(self, parent):
        self.curl_text = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("导入 curl 命令")
        self.dialog.geometry("700x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        ttk.Label(self.dialog, text="粘贴 curl 命令（支持 -X, -H, -d, -u, -b, --url 等常用选项）:").pack(anchor=tk.W, padx=10, pady=(15, 5))

        self.text = scrolledtext.ScrolledText(self.dialog, wrap=tk.WORD, height=14, font=("Consolas", 10))
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.text.focus()

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)

        self.dialog.bind('<Control-Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())

    def ok_clicked(self):
        raw = self.text.get(1.0, tk.END).strip()
        if not raw:
            messagebox.showwarning("警告", "请粘贴 curl 命令", parent=self.dialog)
            return
        self.curl_text = raw
        self.dialog.destroy()

    def cancel_clicked(self):
        self.curl_text = None
        self.dialog.destroy()


class HistoryPanel:
    """历史记录侧边栏面板"""

    def __init__(self, parent, db, on_select_request):
        self.db = db
        self.on_select_request = on_select_request
        self.selected_category = tk.StringVar()

        # 创建面板
        self.frame = ttk.Frame(parent)
        self.frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        self.create_widgets()

    def create_widgets(self):
        """创建面板内容"""
        # 标题
        title_label = ttk.Label(self.frame, text="历史记录", font=("Arial", 10, "bold"))
        title_label.pack(pady=(0, 10))

        # 分类选择
        category_frame = ttk.Frame(self.frame)
        category_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(category_frame, text="分类:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.selected_category,
                                          state="readonly", width=15)
        self.category_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        self.load_categories()

        # 搜索框
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X)
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # 历史记录列表
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ('method', 'url')
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=20)
        self.tree.heading("#0", text="名称")
        self.tree.heading("method", text="方法")
        self.tree.heading("url", text="URL")
        self.tree.column("#0", width=150)
        self.tree.column("method", width=60)
        self.tree.column("url", width=250)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 双击加载
        self.tree.bind('<Double-1>', self.on_item_double_click)

        # 按钮
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="刷新", command=self.refresh).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="删除", command=self.delete_request).pack(fill=tk.X)

        # 初始加载
        self.refresh()

    def load_categories(self):
        """加载分类列表"""
        categories = self.db.get_categories()
        category_names = [cat['name'] for cat in categories]
        self.category_combo['values'] = category_names
        if category_names:
            self.category_combo.set(category_names[0])
            self.selected_category.set(category_names[0])

    def refresh(self):
        """刷新历史记录列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取请求记录
        category = self.selected_category.get()
        requests = self.db.get_all_requests(category)

        # 添加到列表
        for req in requests:
            self.tree.insert("", tk.END, text=req['name'],
                           values=(req['method'], req['url']),
                           tags=(req['id'],))

    def on_category_change(self, event=None):
        """分类改变事件"""
        self.refresh()

    def on_search(self, event=None):
        """搜索事件"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self.refresh()
            return

        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 搜索
        results = self.db.search_requests(keyword)
        for req in results:
            self.tree.insert("", tk.END, text=req['name'],
                           values=(req['method'], req['url']),
                           tags=(req['id'],))

    def on_item_double_click(self, event=None):
        """双击加载请求"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        request_id = self.tree.item(item, 'tags')[0]

        request_data = self.db.get_request_by_id(request_id)
        if request_data and self.on_select_request:
            self.on_select_request(request_data)

    def delete_request(self):
        """删除请求记录"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的记录")
            return

        if messagebox.askyesno("确认", "确定要删除这条记录?"):
            item = selection[0]
            request_id = self.tree.item(item, 'tags')[0]
            self.db.delete_request(request_id)
            self.refresh()

class HTTPClientApp:
    """主应用程序类"""

    def __init__(self, root):
        self.root = root
        self.root.title("HTTP客户端")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)

        # 初始化数据库
        self.db = HistoryDB()

        # 创建菜单栏
        self.create_menu()

        # 创建主界面
        self.create_main_interface()

        # 绑定快捷键
        self.root.bind('<Control-n>', lambda e: self.new_tab())
        self.root.bind('<Control-s>', lambda e: self.save_current_request())
        self.root.bind('<Control-Return>', lambda e: self.send_current_request())

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建请求 (Ctrl+N)", command=self.new_tab)
        file_menu.add_separator()
        file_menu.add_command(label="导入 curl", command=self.import_curl)
        file_menu.add_command(label="导入请求", command=self.import_requests)
        file_menu.add_command(label="导出请求", command=self.export_requests)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 请求菜单
        req_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="请求", menu=req_menu)
        req_menu.add_command(label="发送 (Ctrl+Enter)", command=self.send_current_request)
        req_menu.add_command(label="保存请求 (Ctrl+S)", command=self.save_current_request)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_main_interface(self):
        """创建主界面"""
        # 创建PanedWindow
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧：请求标签页区域
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)

        # 右侧：历史记录面板
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # 创建可关闭的标签页容器
        self.notebook = ClosableNotebook(left_frame, on_close_tab=self.close_tab)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 标签页管理
        self.tabs = {}  # 存储所有标签页实例

        # 创建工具栏
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="新建请求", command=self.new_tab).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="导入 curl", command=self.import_curl).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="发送", command=self.send_current_request).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="保存", command=self.save_current_request).pack(side=tk.LEFT)

        # 创建历史记录面板
        self.history_panel = HistoryPanel(right_frame, self.db, self.load_request_to_tab)

        # 创建第一个标签页
        self.new_tab()

    def new_tab(self):
        """创建新标签页"""
        tab_count = len(self.notebook.tabs()) + 1
        tab_name = f"请求 {tab_count}"

        # 创建新标签页实例
        tab = RequestTab(self.notebook, self.db, tab_name)

        # 使用框架对象作为键存储
        self.tabs[tab.frame] = tab

        # 选择新标签页
        self.notebook.select(tab.frame)
        return tab

    def close_tab(self, tab_id, tab_frame):
        """关闭标签页回调函数"""
        # 从映射中删除
        for frame, tab in list(self.tabs.items()):
            if str(frame) == tab_id:
                del self.tabs[frame]
                break

        # 如果关闭的是当前标签页，切换到其他标签页
        current = self.notebook.select()
        if current == tab_id:
            # 选择其他标签页
            remaining_tabs = self.notebook.tabs()
            if remaining_tabs:
                self.notebook.select(remaining_tabs[0])

    def on_tab_changed(self, event):
        """标签页改变事件"""
        pass

    def get_current_tab(self):
        """获取当前标签页"""
        current_tab_id = self.notebook.select()
        if not current_tab_id:
            return None

        # 查找对应的标签页实例
        for frame, tab in self.tabs.items():
            if str(frame) == current_tab_id:
                return tab
        return None

    def send_current_request(self):
        """发送当前标签页的请求"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.send_request()

    def save_current_request(self):
        """保存当前请求"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.save_request()

    def load_request_to_tab(self, request_data):
        """加载请求数据到当前标签页"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.load_request_data(request_data)
            messagebox.showinfo("提示", "请求已加载到当前标签页")

    def import_curl(self):
        """导入 curl 命令：解析后在新标签页展示完整请求"""
        dialog = ImportCurlDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if not dialog.curl_text:
            return
        try:
            request_data = parse_curl_command(dialog.curl_text)
        except ValueError as e:
            messagebox.showerror("解析失败", str(e))
            return
        # 新建标签页并填充
        tab = self.new_tab()
        tab.load_request_data(request_data)
        short_url = request_data['url']
        if len(short_url) > 30:
            short_url = short_url[:27] + "..."
        tab_name = f"{request_data['method']} {short_url}"
        current_tab_id = self.notebook.select()
        if current_tab_id:
            self.notebook.set_tab_text(current_tab_id, tab_name)
        messagebox.showinfo("成功", "curl 已解析并加载到新标签页")

    def import_requests(self):
        """导入请求记录"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="导入请求记录",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            count = self.db.import_requests(file_path)
            messagebox.showinfo("成功", f"成功导入 {count} 条记录")
            self.history_panel.refresh()

    def export_requests(self):
        """导出请求记录"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="导出请求记录",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        if file_path:
            count = self.db.export_requests(file_path)
            messagebox.showinfo("成功", f"成功导出 {count} 条记录")

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于",
                          "HTTP客户端工具\n"
                          "版本: 2.0 \n"
                          "功能: 支持多标签页、历史记录、分类管理\n"
                          "开发者: Claude")

def main():
    root = tk.Tk()
    app = HTTPClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
