# 服务器代理配置指南

## 问题
服务器上运行时，Python 代码调用 AI API 超时，但 curl 直接调用正常。

## 解决方案

### 第一步：检查服务器当前的代理配置
```bash
# 查看代理变量
echo $HTTP_PROXY
echo $HTTPS_PROXY
echo $http_proxy
echo $https_proxy
```

### 第二步：在 systemd 服务文件中添加代理配置

编辑 `/etc/systemd/system/agent_check.service`，在 `[Service]` 部分添加：

```ini
# 添加代理配置（替换为你的实际代理地址）
Environment=HTTP_PROXY=http://your-proxy:port
Environment=HTTPS_PROXY=http://your-proxy:port
```

或者如果不需要代理：
```ini
# 不使用代理（通常不推荐，除非网络直接通）
Environment=NO_PROXY=localhost,127.0.0.1
```

### 第三步：完整的 systemd 服务文件示例
```ini
[Unit]
Description=Teaching AI Agent Server
After=syslog.target network.target nfs-client.target

[Service]
Type=simple
WorkingDirectory=/gaojj/agent_check
Environment=HOST=0.0.0.0
Environment=PORT=8001
Environment=RELOAD=false
# 【新增】添加代理配置
Environment=HTTP_PROXY=http://your-proxy:port
Environment=HTTPS_PROXY=http://your-proxy:port
ExecStart=/gaojj/agent_check/.venv/bin/python -u /gaojj/agent_check/server.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
StandardOutput=append:/gaojj/agent_check/logs/server.log
StandardError=append:/gaojj/agent_check/logs/server.log

[Install]
WantedBy=multi-user.target
```

### 第四步：更新并重启服务
```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 重启服务
sudo systemctl restart agent_check

# 查看服务状态
sudo systemctl status agent_check

# 查看实时日志
sudo tail -f /gaojj/agent_check/logs/server.log
```

### 第五步：验证代理是否生效
查看日志中是否有以下信息：
```
[INFO] 使用代理配置 - HTTP_PROXY: http://..., HTTPS_PROXY: http://...
```

### 快速测试
```bash
# 测试 API 是否正常（使用与代码相同的代理）
curl -X POST https://ark.cn-beijing.volces.com/api/v3/chat/completions \
  -H "Authorization: Bearer a3bc8e8a-bef1-4ff2-9f0d-2d539772b809" \
  -H "Content-Type: application/json" \
  -d '{"model":"ep-20260518113327-5rkl7","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

## 代码已修改的内容
✅ `mafs_backend.py` 已更新：
- 自动检测并使用系统代理环境变量
- 打印代理配置信息到日志
- 让 openai 库自动使用代理

## 常见代理地址示例
```
# 本地代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# 局域网代理
HTTP_PROXY=http://192.168.1.100:8080
HTTPS_PROXY=http://192.168.1.100:8080
```
