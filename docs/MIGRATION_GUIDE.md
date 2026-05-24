
# MySQL 数据库迁移指南

## 一、架构变更说明

### 原架构
- 使用 `SqliteSaver` 自动持久化 LangGraph 状态
- 数据库文件：`teacher_workshop.db`（SQLite）

### 新架构
- 采用 SQLAlchemy ORM + MySQL 数据库
- **读写分离**：主库负责写入，从库负责读取
- 使用 `MemorySaver` 临时保存会话状态（运行时），消息完成后持久化到 MySQL

---

## 二、数据库表结构

### 1. `workshop_sessions` - 教研会话表
| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | VARCHAR(64) | 会话ID（主键），由前端生成 |
| `user_id` | VARCHAR(64) | 用户ID（索引） |
| `teacher_name` | VARCHAR(100) | 教师姓名 |
| `lesson_info` | JSON | 课例信息字典 |
| `report_summary` | TEXT | 课堂观察报告内容 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_active` | TINYINT | 是否活跃（1=活跃，0=已结束） |

### 2. `dialogue_records` - 对话历史表
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT | 自增主键 |
| `session_id` | VARCHAR(64) | 会话ID（外键） |
| `role` | VARCHAR(32) | 角色标识（user/peer/expert/mentor） |
| `role_name` | VARCHAR(100) | 角色名称（中文） |
| `content` | TEXT | 消息内容 |
| `created_at` | DATETIME | 创建时间 |

### 3. `discussion_reports` - 研讨报告表
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT | 自增主键 |
| `session_id` | VARCHAR(64) | 会话ID（外键，唯一） |
| `report_content` | TEXT | 研讨报告全文 |
| `created_at` | DATETIME | 创建时间 |

---

## 三、环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
# 编辑 .env 文件
```

**数据库配置示例**：

```env
# 单库模式（读写都用一个库）
MYSQL_MASTER_URL=mysql+pymysql://root:password@127.0.0.1:3306/teacher_workshop_db
MYSQL_SLAVE_URL=mysql+pymysql://root:password@127.0.0.1:3306/teacher_workshop_db

# 主从分离模式
MYSQL_MASTER_URL=mysql+pymysql://root:password@192.168.1.100:3306/teacher_workshop_db
MYSQL_SLAVE_URL=mysql+pymysql://root:password@192.168.1.101:3306/teacher_workshop_db
```

---

## 四、部署步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 创建 MySQL 数据库
```sql
CREATE DATABASE teacher_workshop_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 初始化表结构
```bash
python init_db.py
```

### 4. 启动服务
```bash
python server.py
# 或使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8001
```

---

## 五、API 接口变更

### `POST /chat` 变更
**新增字段**：`user_id`
**重命名字段**：`report_id` → `session_id`

```json
{
  "session_id": "abc123",
  "user_id": "user001",
  "message": "你好",
  "teacher_name": "李老师",
  "lesson_info": {"学科": "语文", "年级": "三年级"},
  "report_content": "课堂观察报告..."
}
```

### `POST /terminate` 变更
**新增字段**：`user_id`
**重命名字段**：`report_id` → `session_id`

### 新增 `GET /api/session/{session_id}`
获取会话完整信息（读操作，从从库读取）

---

## 六、数据迁移（可选）

如果需要从原有 SQLite 数据库迁移数据：

```python
# 可以编写迁移脚本读取旧的 SQLite 数据并写入新的 MySQL
# SqliteSaver 的数据在 checkpoints 表中
```

---

## 七、注意事项

1. **会话生命周期**：每次刷新页面生成新 `session_id`，旧会话 `is_active` 设为 0
2. **读写分离**：查询使用 `get_slave_session()`，写入使用 `get_master_session()`
3. **连接池**：已配置连接池（pool_size=10, max_overflow=20）
4. **兼容模式**：如果没有主从，可以让 slave_url 等于 master_url

