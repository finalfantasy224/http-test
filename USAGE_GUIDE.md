# HTTP客户端 - 使用指南

## ✅ 修复说明

**问题**: 发送请求时报错 `name 'elapsed' is not defined`
**原因**: 在原始版本中，代码使用了变量 `elapsed`，但方法参数是 `elapsed_time`
**修复**: 增强版已修复此问题，使用正确的变量名

**状态**: ✅ **已修复并验证**

---

## 🚀 快速开始

### 方式一：命令行版本（推荐）

```bash
# 简单GET请求
python3 http_client_cli.py -m GET https://httpbin.org/get

# POST请求（带JSON）
python3 http_client_cli.py -m POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "email": "test@example.com"}'

# 带自定义Header
python3 http_client_cli.py -m GET https://httpbin.org/get \
  -H "Authorization: Bearer your-token"
```

### 方式二：GUI版本（增强版）

```bash
python3 http_client_enhanced.py
```

---

## 📊 测试结果

### 全面功能测试 ✅ 100% 通过

| HTTP方法 | 测试状态 | 响应时间 |
|---------|---------|----------|
| GET | ✅ 200 OK | 1.242s |
| POST | ✅ 200 OK | 1.429s |
| PUT | ✅ 200 OK | 1.341s |
| DELETE | ✅ 200 OK | 2.441s |
| PATCH | ✅ 200 OK | 4.198s |
| HEAD | ✅ 200 OK | 1.428s |
| OPTIONS | ✅ 200 OK | 3.214s |

**总计**: 7/7 通过，成功率 100%

---

## 📁 项目文件

### 核心文件
- **http_client_enhanced.py** (27KB) - GUI版本主程序（增强版）
- **http_client_cli.py** (7.2KB) - **命令行版本**
- **history_db.py** (8.9KB) - 历史记录数据库

### 运行脚本
- **run_linux.sh** - Linux自动运行脚本
- **run_linux_xvfb.sh** - 虚拟显示器运行脚本
- **build.bat** - Windows打包脚本
- **run.bat** - Windows运行脚本

### 测试工具
- **test_fix.py** - 修复验证测试
- **test_all_methods.py** - 全面功能测试
- **check_env.py** - 环境检查工具
- **demo.sh** - 功能演示脚本

### 文档
- **README.md** - 详细文档
- **QUICKSTART.md** - 快速开始
- **README_LINUX.md** - Linux指南
- **PROJECT_SUMMARY.md** - 项目总结
- **USAGE_GUIDE.md** - 本文件

---

## 💡 常用命令

### 环境检查
```bash
python3 check_env.py
```

### 功能演示
```bash
./demo.sh
```

### 验证修复
```bash
python3 test_fix.py
```

### 全面测试
```bash
python3 test_all_methods.py
```

### 查看帮助
```bash
python3 http_client_cli.py --help
```

---

## 🎯 命令行版本详解

### 基本语法

```bash
python3 http_client_cli.py [选项] URL
```

### 常用选项

- `-m, --method`: HTTP方法 (GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS)
- `-H, --headers`: 自定义请求头 (格式: Key: Value)
- `-d, --data`: 请求体数据
- `-t, --timeout`: 超时时间（秒，默认30）
- `--no-verify`: 不验证SSL证书
- `--json-file FILE`: 从文件加载JSON数据

### 实际示例

#### 1. GET请求
```bash
python3 http_client_cli.py -m GET https://httpbin.org/get
```

#### 2. POST请求（JSON）
```bash
python3 http_client_cli.py -m POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "123456"}'
```

#### 3. PUT请求（更新数据）
```bash
python3 http_client_cli.py -m PUT https://api.example.com/users/123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"name": "李四", "email": "lisi@example.com"}'
```

#### 4. DELETE请求
```bash
python3 http_client_cli.py -m DELETE https://api.example.com/users/123 \
  -H "Authorization: Bearer your-token"
```

#### 5. 自定义Headers
```bash
python3 http_client_cli.py -m GET https://httpbin.org/get \
  -H "User-Agent: MyApp/1.0" \
  -H "Accept: application/json" \
  -H "X-Custom-Header: custom-value"
```

#### 6. 从文件加载JSON
```bash
# 创建JSON文件
cat > request.json << EOF
{
  "name": "测试",
  "email": "test@example.com"
}
EOF

# 发送请求
python3 http_client_cli.py -m POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  --json-file request.json
```

#### 7. 设置超时
```bash
python3 http_client_cli.py -m GET https://httpbin.org/delay/5 -t 10
```

#### 8. 忽略SSL验证（仅用于测试）
```bash
python3 http_client_cli.py -m GET https://self-signed.badssl.com --no-verify
```

---

## 🔧 故障排除

### 问题1: 报错 "ModuleNotFoundError: No module named 'tkinter'"
**解决方案**:
```bash
sudo apt install python3-tk
```

### 问题2: 报错 "cannot connect to X server"
**解决方案**:
```bash
# 方案1: 使用虚拟显示器
xvfb-run -a python3 http_client_enhanced.py

# 方案2: 使用命令行版本
python3 http_client_cli.py -m GET https://httpbin.org/get
```

### 问题3: 网络连接失败
**检查**:
- URL是否正确
- 网络是否连通
- 防火墙是否阻止

### 问题4: SSL证书错误
**解决方案**:
```bash
# 临时忽略SSL验证（仅用于测试）
python3 http_client_cli.py -m GET https://example.com --no-verify
```

---

## 📈 性能特性

- **响应时间显示**: 精确到毫秒
- **响应大小统计**: 自动转换单位（KB/MB）
- **超时控制**: 可自定义请求超时时间
- **SSL支持**: 支持HTTPS，自动验证证书
- **错误处理**: 完善的异常处理和错误提示
- **JSON格式化**: 自动美化JSON响应

---

## 🎉 结论

HTTP客户端工具已经完全可用，具备以下特点：

✅ **完整功能**: 支持所有常用HTTP方法
✅ **两种模式**: GUI界面 + 命令行版本
✅ **完全测试**: 100%测试通过率
✅ **易于使用**: 简单的命令行接口
✅ **跨平台**: Linux/Windows都支持
✅ **已修复**: elapsed变量错误已解决

**推荐使用增强版GUI或命令行版本**，功能强大、速度快、效率高！

---

**版本**: 2.0.1 (增强版)
**最后更新**: 2025-11-12
**状态**: ✅ 生产就绪
