
#!/bin/bash

echo "=== 教研AI Agent MySQL 版本部署脚本 ==="
echo ""

# 检查 Python
if ! command -v python3 &amp;&gt; /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查 config.yaml 文件
if [ ! -f "config.yaml" ]; then
    echo "⚠️  警告: 未找到 config.yaml 文件！"
    exit 0
fi

echo "1️⃣  安装依赖包..."
pip install -r requirements.txt

echo ""
echo "2️⃣  初始化数据库表结构..."
python init_db.py

echo ""
echo "3️⃣  启动服务..."
echo "   服务将在 http://localhost:8001 启动"
python server.py

