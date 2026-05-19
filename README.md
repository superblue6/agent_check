# 教研AI Agent Server

基于 FastAPI 和 LangGraph 的智能教研助手，支持多个 AI 角色（教学同伴、教育专家、资深教研员）协同开展教研活动。

## 功能特性

- 🤖 **多角色 AI 助手**：教学同伴、教育专家、资深教研员
- 💬 **智能对话路由**：自动根据用户意图分配合适的 AI 角色
- 📊 **自动生成报告**：汇总对话内容，生成结构化教研报告
- 🔄 **会话历史管理**：基于 SQLite 的断点续传机制
- 🌐 **跨平台部署**：支持 Linux/Windows 服务器部署

## 技术栈

- **后端框架**：FastAPI + Uvicorn
- **AI 框架**：LangGraph + LangChain
- **语言模型**：DeepSeek（通过火山引擎 API）
- **数据库**：SQLite
- **部署方式**：Systemd 服务

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/superblue6/agent_check.git
cd agent_check
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
# 火山引擎 API 配置
ARK_API_KEY=your_ark_api_key_here
ARK_API_BASE=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=ep-20260518113327-5rkl7

# 可选配置
LANGCHAIN_API_KEY=your_langchain_key_here
LANGCHAIN_TRACING_V2=false

# 服务配置
HOST=0.0.0.0
PORT=8001
RELOAD=false
```

### 4. 本地运行

```bash
# 方式 1：直接运行
python server.py

# 方式 2：使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8001
```

服务启动后访问：
- API 文档：http://localhost:8001/docs
- 前端页面：http://localhost:8001/

## API 使用

### 发送聊天消息

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "lesson_001",
    "message": "你好，我想讨论一下这节课的教学设计",
    "teacher_name": "张老师",
    "lesson_info": {
      "subject": "初中数学",
      "grade": "七年级",
      "topic": "一元二次方程"
    },
    "report_content": "课堂观察报告内容..."
  }'
```

### 生成研讨报告

```bash
curl -X POST http://localhost:8001/terminate \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "lesson_001",
    "teacher_name": "张老师",
    "lesson_info": {
      "subject": "初中数学",
      "grade": "七年级"
    }
  }'
```

## 服务器部署（Linux）

### 1. 安装依赖

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. 配置服务

```bash
# 复制 service 文件
sudo cp agent_check.service /etc/systemd/system/

# 创建目录
sudo mkdir -p /gaojj/agent_check/logs
sudo touch /gaojj/agent_check/logs/server.log

# 重新加载 systemd
sudo systemctl daemon-reload
```

### 3. 启动服务

```bash
# 启动
sudo systemctl start agent_check

# 设置开机自启
sudo systemctl enable agent_check

# 查看状态
sudo systemctl status agent_check

# 查看日志
sudo journalctl -u agent_check -f
```

## 项目结构

```
agent_check/
├── server.py              # FastAPI 服务入口
├── mafs_backend.py        # AI Agent 核心逻辑
├── mafs_frontend.html    # 前端页面
├── requirements.txt      # Python 依赖
├── agent_check.service   # systemd 服务配置
├── .env                  # 环境变量（不提交到 Git）
├── env.example           # 环境变量模板
└── logs/                 # 日志目录
    └── server.log        # 服务日志
```

## AI 角色说明

### 教学同伴 (peer)
- 引导老师还原课堂细节
- 多问学生反应、掌握情况
- 不直接给建议

### 教育专家 (expert)
- 用教育理论解释课堂现象
- 结合报告做简短分析
- 100字以内，专业易懂

### 资深教研员 (mentor)
- 给出具体可操作的教学建议
- 每次1-2条建议
- 100字以内

## 获取 API Key

### 火山引擎（必需）

1. 访问：https://console.volcengine.com
2. 注册/登录账号
3. 创建 API Key
4. 复制 Key 到 `.env` 文件

### 火山引擎 DeepSeek 模型

- **模型名称**：`ep-20260518113327-5rkl7`（示例）
- **API 端点**：`https://ark.cn-beijing.volces.com/api/v3`
- **计费方式**：按 token 计费

## 常见问题

### Q1: 服务启动失败
```bash
# 检查日志
sudo journalctl -u agent_check -n 50

# 检查端口占用
sudo lsof -i :8001
```

### Q2: API 连接超时
- 检查服务器网络是否能访问火山引擎
- 检查 API Key 是否正确
- 查看 API 配额是否充足

### Q3: 数据库锁定
```bash
# 删除锁文件
rm -f teacher_workshop.db-*
```

## 开发指南

### 运行测试
```bash
# 测试 API 连接
python -c "from mafs_backend import model; print(model.invoke('你好'))"
```

### 查看日志
```bash
# 实时日志
tail -f logs/server.log

# 错误日志
grep ERROR logs/server.log
```

## License

MIT License

## 联系方式

- GitHub Issues：https://github.com/superblue6/agent_check/issues
- 邮箱：your.email@example.com
