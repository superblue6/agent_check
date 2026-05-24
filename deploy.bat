
@echo off
echo === 教研AI Agent MySQL 版本部署脚本 ===
echo.

REM 检查 config.yaml 文件
if not exist "config.yaml" (
    echo ⚠️  警告: 未找到 config.yaml 文件！
    pause
    exit /b 0
)

echo 1️⃣  安装依赖包...
pip install -r requirements.txt

echo.
echo 2️⃣  初始化数据库表结构...
python init_db.py

echo.
echo 3️⃣  启动服务...
echo    服务将在 http://localhost:8001 启动
python server.py

pause
