# AI 模型 API 连接超时问题排查

## 问题现象
服务器调用 AI 模型时出现连接超时：
```
httpcore.ConnectError: [Errno 110] Connection timed out
```

## 排查步骤

### 1. 测试网络连通性

在服务器上执行以下命令：

```bash
# 测试 DNS 解析
nslookup ark.cn-beijing.volces.com

# 测试 TCP 连接（应该看到 "Connected" 或类似信息）
timeout 10 curl -v https://ark.cn-beijing.volces.com/api/v3 2>&1 | head -30

# 测试网络路由
traceroute ark.cn-beijing.volces.com

# ping 测试（可能ICMP被禁用）
ping -c 3 ark.cn-beijing.volces.com
```

### 2. 检查代理配置

如果服务器在中国大陆境外，可能需要设置代理：

```bash
# 查看当前代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
echo $http_proxy
echo $https_proxy

# 如果需要设置代理，在 systemd service 中添加：
# Environment=HTTP_PROXY=http://your-proxy:port
# Environment=HTTPS_PROXY=http://your-proxy:port
```

### 3. 检查防火墙规则

```bash
# 检查 iptables 规则
sudo iptables -L -n | grep -E "443|ACCEPT|DROP"

# 检查是否阻止了出站 HTTPS
sudo iptables -L OUTPUT -n

# 如果服务器在云上，检查安全组规则
# AWS: 检查 EC2 安全组
# 阿里云: 检查安全组规则
```

### 4. 检查服务器网络配置

```bash
# 检查网络接口
ip addr show

# 检查默认路由
ip route show

# 检查 DNS 配置
cat /etc/resolv.conf

# 测试 DNS 解析速度
time nslookup ark.cn-beijing.volces.com
```

### 5. 测试 OpenAI 客户端直接连接

创建一个测试脚本 `test_api.py`：

```python
import os
from langchain_openai import ChatOpenAI

deepseek_key = "a3bc8e8a-bef1-4ff2-9f0d-2d539772b809"

model = ChatOpenAI(
    model="ep-20260518113327-5rkl7",
    openai_api_key=deepseek_key,
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    max_tokens=10,
    timeout=30,  # 增加超时时间
)

try:
    response = model.invoke("你好")
    print(f"成功: {response.content}")
except Exception as e:
    print(f"错误: {e}")
```

运行测试：
```bash
cd /gaojj/agent_check
.venv/bin/python test_api.py
```

### 6. 检查 API 端点是否正确

确认使用的 API 端点：
- 当前：`https://ark.cn-beijing.volces.com/api/v3`
- 备选：`https://ark.cn-beijing.volcn.com/api/v3`

### 7. 检查 API 配额和余额

登录火山引擎控制台检查：
- API 配额是否用完
- 账户余额是否充足
- API Key 是否有效

## 常见原因

### 原因 1：服务器在境外需要代理
**症状**：DNS 解析成功，但 TCP 连接超时
**解决**：设置 HTTP/HTTPS 代理

### 原因 2：防火墙阻止出站连接
**症状**：ping 成功，但 443 端口无法连接
**解决**：开放 443 端口的出站规则

### 原因 3：网络路由问题
**症状**：部分 IP 可以访问，部分不行
**解决**：使用代理或更换服务器位置

### 原因 4：API 端点不可达
**症状**：特定域名超时
**解决**：检查 API 端点地址，或使用 VPN

### 原因 5：服务器 DNS 污染
**症状**：解析到错误 IP
**解决**：修改 /etc/resolv.conf 使用 Google DNS

## 临时解决方案

### 如果暂时无法修复网络问题

可以在代码中添加更长的超时时间：

```python
model = ChatOpenAI(
    model="ep-20260518113327-5rkl7",
    openai_api_key=deepseek_key,
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    max_tokens=4096,
    temperature=0.3,
    timeout=120,  # 增加超时时间到 120 秒
)
```

这样可以让请求有更多时间完成连接。
