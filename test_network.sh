#!/bin/bash
# 测试 API 连通性脚本

echo "=== 1. 测试 DNS 解析 ==="
nslookup ark.cn-beijing.volces.com

echo ""
echo "=== 2. 测试 TCP 连接 ==="
timeout 10 curl -v https://ark.cn-beijing.volces.com/api/v3 2>&1 | head -30

echo ""
echo "=== 3. 检查网络接口 ==="
ip route show

echo ""
echo "=== 4. 检查防火墙 ==="
sudo systemctl status firewalld
sudo iptables -L -n | head -20

echo ""
echo "=== 5. 测试代理（如果有） ==="
echo $HTTP_PROXY
echo $HTTPS_PROXY
echo $http_proxy
echo $https_proxy

echo ""
echo "=== 6. 尝试直接 ping ==="
ping -c 3 ark.cn-beijing.volces.com
