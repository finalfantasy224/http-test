#!/bin/bash

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         🎉 HTTP客户端增强版 - 功能演示                           ║
║                                                                  ║
║              (多标签页 + 历史记录)                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

EOF

echo "📋 功能演示菜单"
echo "═══════════════════════════════════════════════════════════════════"
echo
echo "  1. 启动增强版GUI (推荐)"
echo "     • 多标签页支持"
echo "     • 历史记录管理"
echo "     • 分类和搜索"
echo
echo "  2. 测试所有HTTP方法"
echo "     • GET / POST / PUT"
echo "     • DELETE / PATCH"
echo "     • HEAD / OPTIONS"
echo
echo "  3. 查看功能文档"
echo
echo "  4. 退出"
echo
echo "═══════════════════════════════════════════════════════════════════"

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo
        echo "🚀 启动增强版HTTP客户端..."
        echo
        echo "  功能特点:"
        echo "    ✓ 多标签页 - 同时测试多个API"
        echo "    ✓ 历史记录 - 保存和查看请求历史"
        echo "    ✓ 分类管理 - 按项目分类组织请求"
        echo "    ✓ 快速搜索 - 快速查找历史请求"
        echo
        echo "  快捷键:"
        echo "    Ctrl+N - 新建标签页"
        echo "    Ctrl+S - 保存请求"
        echo "    Ctrl+Enter - 发送请求"
        echo
        python3 http_client_enhanced.py
        ;;
    2)
        echo
        echo "🧪 运行所有HTTP方法测试..."
        python3 test_all_methods.py
        ;;
    3)
        echo
        echo "📖 查看功能文档..."
        echo
        echo "  增强版功能说明:"
        cat ENHANCED_FEATURES.md | head -50
        ;;
    4)
        echo
        echo "👋 退出演示"
        exit 0
        ;;
    *)
        echo
        echo "❌ 无效选择"
        exit 1
        ;;
esac
