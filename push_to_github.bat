@echo off
chcp 65001 > nul
echo ========================================
echo GitHub 代码推送脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查 Git 状态...
git status
echo.

echo [2/3] 推送到 GitHub...
echo 请输入你的 GitHub 用户名和 Personal Access Token
echo.
echo 如果你没有 Token，请按以下步骤获取：
echo 1. 登录 https://github.com
echo 2. Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
echo 3. Generate new token (classic)
echo 4. 勾选 repo 权限
echo 5. 生成后复制 Token
echo.

git push -u origin main

echo.
echo ========================================
echo 推送完成！
echo ========================================
pause
