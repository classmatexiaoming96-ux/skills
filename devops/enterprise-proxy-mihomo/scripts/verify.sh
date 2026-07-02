#!/bin/bash
# verify.sh — 验证代理链路
set -euo pipefail

CONFIG_ENV="/etc/mihomo/env.sh"
[ -f "$CONFIG_ENV" ] && source "$CONFIG_ENV"

HTTP_PORT="${MIHOMO_HTTP_PORT:-7890}"
PROXY="http://127.0.0.1:${HTTP_PORT}"

echo "1. Mihomo 进程"
pgrep -x mihomo > /dev/null && echo "  运行中" || { echo "  未运行"; exit 1; }

echo "2. 端口监听"
for port in ${HTTP_PORT} ${MIHOMO_SOCKS_PORT:-7891} ${MIHOMO_API_PORT:-9090}; do
    ss -tlnp 2>/dev/null | grep -q ":$port " && echo "  :$port  OK" || echo "  :$port  N/A"
done

echo "3. HTTP 代理"
curl -sS --connect-timeout 10 -x "$PROXY" -o /dev/null -w "%{http_code} (%{time_total}s)\n" \
  "http://www.gstatic.com/generate_204" 2>/dev/null || echo "  失败"

echo "4. HTTPS"
curl -sS --connect-timeout 10 -x "$PROXY" -o /dev/null -w "%{http_code} (%{time_total}s)\n" \
  "https://api.github.com" 2>/dev/null || echo "  失败"

echo "5. 出口 IP"
OUTPUT=$(curl -sS --connect-timeout 10 -x "$PROXY" "https://httpbin.org/ip" 2>/dev/null || true)
echo "  ${OUTPUT:-查询失败}"

echo "完成"
