# 教研AI Agent 部署说明

## 1. 上传项目文件到服务器

将项目文件上传到服务器的 `/gaojj/agent_check` 目录。

## 2. 创建虚拟环境并安装依赖

```bash
cd /gaojj/agent_check

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 3. 配置端口和主机（可选）

如需修改端口或允许外部访问，可以在代码中设置，或使用环境变量：

```bash
export HOST=0.0.0.0
export PORT=8001
```

## 4. 创建日志目录

```bash
mkdir -p /gaojj/agent_check/logs
```

## 5. 部署 systemd 服务

### 复制服务文件
```bash
cp /gaojj/agent_check/agent_check.service /etc/systemd/system/
```

### 重载 systemd 配置
```bash
systemctl daemon-reload
```

### 启用并启动服务
```bash
systemctl enable agent_check
systemctl start agent_check
```

## 6. 常用命令

### 查看服务状态
```bash
systemctl status agent_check
```

### 查看服务日志
```bash
journalctl -u agent_check -f
# 或查看应用日志
tail -f /gaojj/agent_check/logs/server.log
```

### 重启服务
```bash
systemctl restart agent_check
```

### 停止服务
```bash
systemctl stop agent_check
```

## 7. 防火墙配置（如需要）

如果需要从外部访问服务，需要开放相应端口：

```bash
# CentOS/RHEL
firewall-cmd --permanent --add-port=8001/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw allow 8001
```

## 8. 验证部署

访问以下地址验证服务是否正常运行：
- 首页：`http://<服务器IP>:8001`
- API文档：`http://<服务器IP>:8001/docs`

