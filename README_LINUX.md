# Linux/Ubuntu 运行指南

## ⚠️ 重要说明

这个HTTP客户端是为Windows设计的GUI应用，使用Tkinter库。在Linux系统上运行需要满足以下条件之一：

## 方案一：桌面环境（推荐）

### 1. 安装依赖

```bash
# 更新包列表
sudo apt update

# 安装Python3和必要组件
sudo apt install -y python3 python3-pip python3-tk

# 安装HTTP客户端依赖
pip3 install -r requirements.txt
```

### 2. 运行程序

```bash
# 使用我们的脚本（自动检测和安装）
./run_linux.sh

# 或直接运行增强版
python3 http_client_enhanced.py

# 或使用演示脚本
./demo_enhanced.sh
```

### 3. 如果使用SSH连接

需要启用X11转发：

```bash
# 连接时使用 -X 参数
ssh -X username@hostname

# 或在ssh配置中启用
ssh -Y username@hostname
```

## 方案二：虚拟显示器（无GUI环境）

如果服务器没有图形界面，可以使用虚拟显示器：

### 1. 安装xvfb

```bash
sudo apt update
sudo apt install -y xvfb python3-tk
pip3 install -r requirements.txt
```

### 2. 运行程序

```bash
# 使用虚拟显示器
xvfb-run -a python3 http_client_enhanced.py

# 或使用我们的脚本
./run_linux_xvfb.sh
```

## 方案三：命令行版本（无GUI）

如果不需要图形界面，我们还有一个命令行版本：

```bash
python3 http_client_cli.py
```

## 方案四：打包为AppImage（跨平台）

可以使用PyInstaller打包成AppImage：

```bash
pip3 install pyinstaller
pyinstaller --onefile --add-data "/usr/lib/python3/dist-packages/tkinter:tkinter" http_client_enhanced.py
```

## 常见问题解决

### Q: 报错"cannot connect to X server"

**A**: 解决方案：
- 使用xvfb虚拟显示器：`xvfb-run -a python3 http_client_enhanced.py`
- 或使用SSH X转发：`ssh -X user@host`

### Q: 报错"ModuleNotFoundError: No module named 'tkinter'"

**A**: 安装tkinter：
```bash
sudo apt install python3-tk
```

### Q: 报错"pip: command not found"

**A**: 安装pip：
```bash
sudo apt install python3-pip
```

### Q: 程序启动慢或卡顿

**A**: 正常现象，首次启动可能较慢，特别是加载GUI库时

## 当前系统检测

运行环境信息：
- 操作系统: Linux
- Python版本: 已检测到
- 图形界面: 需要检测DISPLAY变量
- tkinter: 需要安装

运行检查脚本：
```bash
python3 check_env.py
```

## 测试API示例

程序启动后，可以尝试这些测试：

**GET请求测试**
```
URL: https://httpbin.org/get
方法: GET
```

**POST请求测试**
```
URL: https://httpbin.org/post
方法: POST
Headers:
  Content-Type: application/json
Body:
  {
    "name": "测试用户",
    "email": "test@example.com"
  }
```

## 性能优化建议

1. **在服务器上运行**：考虑使用远程桌面或VNC
2. **使用Docker**：创建带GUI的Docker容器
3. **转换Web版本**：使用Flask/FastAPI创建Web版本

---

如果遇到问题，请查看错误信息并参考上述解决方案。
