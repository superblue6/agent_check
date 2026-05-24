
# 项目架构变更总结 - MySQL 读写分离版本

## 📋 变更概述

本项目已从 SQLite 迁移到 MySQL，并实现了读写分离架构。

---

## 📁 新增文件

| 文件 | 用途 |
|------|------|
| `db_models.py` | 数据库模型定义（三个表 + 读写分离管理器） |
| `init_db.py` | 数据库初始化脚本（创建表结构） |
| `.env.example` | 环境变量配置模板 |
| `MIGRATION_GUIDE.md` | 详细迁移与部署指南 |
| `deploy.sh` | Linux/Mac 快速部署脚本 |
| `deploy.bat` | Windows 快速部署脚本 |
| `PROJECT_CHANGES.md` | 本文档 - 变更总结 |

---

## 🔧 修改文件

| 文件 | 修改内容 |
|------|----------|
| `server.py` | - 替换 `SqliteSaver` 为 `MemorySaver`<br>- 集成 MySQL 持久化<br>- API 接口新增 `user_id`，`report_id` 改为 `session_id`<br>- 新增 `/api/session/{session_id}` 接口<br>- 启动时加载 .env 环境变量 |
| `requirements.txt` | 新增依赖：`sqlalchemy`, `pymysql`, `cryptography`, `python-dotenv` |
| `mafs_backend.py` | 无代码变更（仍可正常使用） |

---

## 🗄️ 数据库设计

### 三表结构

1. **`workshop_sessions`** - 教研会话
   - 主键：`session_id`（前端生成）
   - 关联用户：`user_id`
   - 课例信息、教师姓名等元数据
   - 状态标识：`is_active`（1活跃 / 0已结束）

2. **`dialogue_records`** - 对话历史
   - 外键关联 `session_id`
   - 每条用户和 AI 消息各一条记录
   - 包含角色标识（user/peer/expert/mentor）

3. **`discussion_reports`** - 研讨报告
   - 外键关联 `session_id`（一对一）
   - 保存生成的完整报告

---

## 🚀 部署流程

### Windows 部署
```batch
copy .env.example .env
# 编辑 .env 配置 MySQL
deploy.bat
```

### Linux/Mac 部署
```bash
cp .env.example .env
# 编辑 .env 配置 MySQL
chmod +x deploy.sh
./deploy.sh
```

### 手动部署
```bash
# 1. 配置环境
cp .env.example .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建数据库（MySQL 中执行）
CREATE DATABASE teacher_workshop_db CHARACTER SET utf8mb4;

# 4. 初始化表
python init_db.py

# 5. 启动服务
python server.py
```

---

## 📡 API 接口变更

### `POST /chat`
**请求体变更**
```json
{
  "session_id": "新字段-会话ID",
  "user_id": "新字段-用户ID",  // ← 新增
  "message": "消息内容",
  "teacher_name": "教师姓名",
  "lesson_info": {...},
  "report_content": "..."
}
```
**注意**：原 `report_id` 已更名为 `session_id`

### `POST /terminate`
同样新增 `user_id`，`report_id` 改为 `session_id`

### `GET /api/session/{session_id}` (新增)
获取完整会话记录（从从库读取）

---

## 💡 关键设计决策

1. **临时状态 + 持久化**
   - 对话期间使用 `MemorySaver` 临时保持状态
   - 对话完成后异步保存到 MySQL
   - 避免频繁写入，提升性能

2. **读写分离**
   - `get_master_session()` - 写入操作（/chat, /terminate）
   - `get_slave_session()` - 读取操作（/api/session）
   - 兼容单库模式（slave_url = master_url）

3. **会话隔离**
   - 每次新页面生成新 `session_id`
   - `user_id` 用于区分不同用户
   - 结束会话时 `is_active` 设为 0

---

## 🔍 后续优化建议

- [ ] 添加历史会话列表接口（按 user_id 查询）
- [ ] 添加对话搜索功能
- [ ] 添加数据导出功能（CSV/PDF）
- [ ] 添加缓存层（Redis）降低 DB 压力
- [ ] 添加慢查询日志监控

