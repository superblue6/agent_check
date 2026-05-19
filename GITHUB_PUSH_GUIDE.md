# 🚀 GitHub 上传指南

## 快速开始

### 方法 1：使用 GitHub 网页界面（推荐新手）

1. **打开 GitHub 创建仓库页面**
   访问：https://github.com/new

2. **填写仓库信息**
   - Repository name: `agent_check`
   - Description: `教研AI Agent Server - 基于 FastAPI 和 LangGraph 的智能教研助手`
   - 选择 **Public**（公开）
   - **不要勾选** "Initialize this repository with a README"
   - 点击 **Create repository**

3. **推送本地代码**
   
   在项目目录中执行以下命令（将 `YOUR_USERNAME` 替换为你的 GitHub 用户名）：

   ```bash
   cd "e:\文件\教研部署包\test_v4_ok 2"
   
   # 添加远程仓库
   git remote add origin https://github.com/superblue6/agent_check.git
   
   # 推送代码到 GitHub
   git branch -M main
   git push -u origin main
   ```

4. **输入 GitHub 凭证**
   - 系统会提示输入用户名和密码/Token
   - **密码请使用 Personal Access Token**，不是登录密码！
   - Token 获取方法见下方"获取 GitHub Token"部分

### 方法 2：使用 GitHub CLI（需要安装）

如果你已安装 GitHub CLI，执行：

```bash
# 创建仓库
gh repo create agent_check --public --source=. --remote=origin

# 推送代码
git push -u origin master
```

---

## 📋 获取 GitHub Personal Access Token

### 步骤 1：生成 Token

1. 登录 GitHub：https://github.com
2. 点击右上角头像 → **Settings**
3. 左侧菜单点击 **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token** → **Generate new token (classic)**
6. 填写：
   - **Note**: `agent_check push access`
   - **Expiration**: 选择 `30 days` 或 `90 days`
   - **Select scopes**: ✅ 勾选 `repo` 和 `workflow`
7. 点击 **Generate token**
8. **重要**：立即复制 Token 保存，它只会显示一次！

### 步骤 2：使用 Token 推送

在推送时，系统会要求输入密码，此时粘贴你的 Token：

```bash
Username: superblue6
Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🔧 后续开发流程

### 1. 修改代码后提交

```bash
# 查看修改状态
git status

# 添加修改的文件
git add .

# 提交修改
git commit -m "描述你的修改内容"

# 推送到 GitHub
git push
```

### 2. 拉取最新代码

```bash
git pull origin main
```

### 3. 查看提交历史

```bash
git log --oneline
```

---

## 📝 .env 配置文件说明

推送到 GitHub 后，**不要**上传包含真实 API Key 的 `.env` 文件。

### 在服务器上配置环境变量

**方法 1：创建 .env 文件（推荐）**

在服务器上创建 `/gaojj/agent_check/.env`：

```bash
sudo vim /gaojj/agent_check/.env
```

添加以下内容：

```
# LLM API Configuration
ARK_API_KEY=你的真实API密钥
ARK_API_BASE=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=ep-20260518113327-5rkl7

# LangChain Configuration (Optional)
LANGCHAIN_API_KEY=你的LangChain密钥
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=agent_check

# Server Configuration
HOST=0.0.0.0
PORT=8001
RELOAD=false

# Database Configuration
DB_PATH=teacher_workshop.db
```

**方法 2：在 systemd service 中配置环境变量**

编辑 `/etc/systemd/system/agent_check.service`：

```ini
[Service]
Environment=ARK_API_KEY=你的真实API密钥
Environment=ARK_API_BASE=https://ark.cn-beijing.volces.com/api/v3
Environment=LANGCHAIN_TRACING_V2=false
Environment=HOST=0.0.0.0
Environment=PORT=8001
Environment=RELOAD=false
ExecStart=/gaojj/agent_check/.venv/bin/python -u /gaojj/agent_check/server.py
StandardOutput=append:/gaojj/agent_check/logs/server.log
StandardError=append:/gaojj/agent_check/logs/server.log
Restart=always
```

---

## ⚙️ 部署后端服务到服务器

### 1. 从 GitHub 克隆代码

```bash
# 在服务器上
cd /gaojj
git clone https://github.com/superblue6/agent_check.git agent_check
cd agent_check
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 创建 .env 文件（见上方说明）
vim .env
```

### 4. 部署 systemd 服务

```bash
# 复制 service 文件
sudo cp agent_check.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 创建日志目录
sudo mkdir -p /gaojj/agent_check/logs
sudo touch /gaojj/agent_check/logs/server.log
sudo chmod 666 /gaojj/agent_check/logs/server.log

# 启动服务
sudo systemctl start agent_check

# 设置开机自启
sudo systemctl enable agent_check

# 查看服务状态
sudo systemctl status agent_check
```

---

## 🐛 常见问题

### Q1: 推送时提示 "Authentication failed"

**原因**：密码验证失败
**解决**：
1. 确保使用的是 Personal Access Token，不是登录密码
2. Token 可能已过期，需要重新生成
3. 检查 Token 是否有 `repo` 权限

### Q2: 远程仓库已存在

如果提示 `fatal: remote origin already exists`，执行：

```bash
git remote set-url origin https://github.com/superblue6/agent_check.git
git push -u origin master
```

### Q3: 忽略文件后仍然推送了敏感信息

**重要**：如果已经推送了包含 API Key 的代码，立即：

1. 删除 GitHub 上的仓库
2. 重新创建仓库
3. **在推送前**，确保 `.env` 和 `.gitignore` 已正确配置
4. 更改你的 API Key（火山引擎控制台）

### Q4: 无法连接到 GitHub

**检查网络连接**：
```bash
ping github.com
```

**配置代理**（如果需要）：
```bash
git config --global http.proxy http://proxy:port
git config --global https.proxy https://proxy:port
```

---

## 📚 相关文档

- [API 连接问题排查指南](./API_CONNECTION_GUIDE.md)
- [部署文档](./DEPLOY.md)（如有）

---

## 🔒 安全提醒

1. **永远不要**将真实 API Key 提交到 GitHub
2. 定期更换 API Key
3. 使用环境变量或专门的密钥管理服务
4. 定期检查 GitHub 仓库的提交历史，确保没有敏感信息
