# 快速开始指南

## 🚀 快速上手

### 方式一：直接运行（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行增强版程序
python http_client_enhanced.py
```

### 方式二：使用批处理文件（Windows用户）

```bash
# 直接双击运行
run.bat
```

### 方式三：打包成exe文件

```bash
# 直接双击运行
build.bat
```

打包完成后，可在 `dist` 文件夹找到 `HTTP客户端.exe`

---

## 📋 系统要求

- Python 3.7 或更高版本
- Windows 7/8/10/11
- 网络连接（用于发送HTTP请求）

---

## 🔧 依赖列表

```
requests>=2.31.0
urllib3>=2.0.0
pyinstaller>=5.13.0
```

---

## ✅ 功能测试

运行测试脚本验证环境：

```bash
python test.py
```

---

## 📝 基本使用

1. **GET请求**
   - 选择方法: GET
   - 输入URL: http://httpbin.org/get
   - 点击发送

2. **POST请求**
   - 选择方法: POST
   - 输入URL: http://httpbin.org/post
   - Headers中添加: Content-Type: application/json
   - Body中输入: {"name": "测试"}
   - 点击发送

---

## ❓ 遇到问题？

1. 运行 `python test.py` 检查环境
2. 查看 `README.md` 详细文档
3. 检查网络连接和URL是否正确

---

## 🎯 下一个测试

试试这个GET请求：
- URL: `https://httpbin.org/get`
- 方法: GET

试试这个POST请求：
- URL: `https://httpbin.org/post`
- 方法: POST
- Headers: Content-Type: application/json
- Body:
  ```json
  {
    "username": "admin",
    "password": "123456"
  }
  ```
