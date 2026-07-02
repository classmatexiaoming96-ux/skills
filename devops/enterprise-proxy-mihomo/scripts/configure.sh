#!/bin/bash
# configure.sh — 从 /etc/mihomo/env.sh 生成 Mihomo 配置
set -euo pipefail

CONFIG_ENV="/etc/mihomo/env.sh"
OUTPUT_CONFIG="/etc/mihomo/config.yaml"
SUB_FILE="/tmp/subscription.yaml"

if [ ! -f "$CONFIG_ENV" ]; then
    echo "请先配置 /etc/mihomo/env.sh"
    exit 1
fi
source "$CONFIG_ENV"

[ "$ENTERPRISE_PROXY_IP" = "10.x.x.x" ] && { echo "请填 ENTERPRISE_PROXY_IP"; exit 1; }
[ "$INTERNAL_DNS_1" = "10.x.x.x" ] && { echo "请填 INTERNAL_DNS_1"; exit 1; }
[ "$WEB_UI_SECRET" = "change-me-to-a-random-secret" ] && { echo "请改 WEB_UI_SECRET"; exit 1; }

VPN_SUB_URL=""
[ -f "/etc/mihomo/subscription_url" ] && VPN_SUB_URL=$(cat /etc/mihomo/subscription_url)

if [ -n "$VPN_SUB_URL" ]; then
    if curl -sSL --max-time 15 -o "$SUB_FILE" "$VPN_SUB_URL" 2>/dev/null && [ -s "$SUB_FILE" ]; then
        echo "直连获取订阅成功"
    elif HTTP_PROXY="http://${ENTERPRISE_PROXY_IP}:${ENTERPRISE_PROXY_PORT}" \
         curl -sSL --max-time 15 -o "$SUB_FILE" "$VPN_SUB_URL" 2>/dev/null && [ -s "$SUB_FILE" ]; then
        echo "通过企业代理获取订阅成功"
    else
        echo "无法获取订阅, 跳过"
        VPN_SUB_URL=""
    fi
fi

cat > "$OUTPUT_CONFIG" << CONFIG
# Mihomo 配置 — 由 configure.sh 生成
mixed-port: ${MIHOMO_HTTP_PORT:-7890}
allow-lan: true
bind-address: "*"
mode: rule
log-level: info
ipv6: false
external-controller: 0.0.0.0:${MIHOMO_API_PORT:-9090}
external-ui: /etc/mihomo/ui
secret: "${WEB_UI_SECRET}"
geodata-mode: true
proxies:
  - {name: "corp-proxy", type: http, server: ${ENTERPRISE_PROXY_IP}, port: ${ENTERPRISE_PROXY_PORT}}
CONFIG

if [ -s "$SUB_FILE" ]; then
    python3 << PYEOF
import sys
sub = open("/tmp/subscription.yaml").read()
cfg = open("/etc/mihomo/config.yaml").read()
lines = sub.split('\n')
nodes = []
in_p = False
for line in lines:
    s = line.strip()
    if s == 'proxies:':
        in_p = True; continue
    if in_p:
        if s.startswith('- ') and 'name:' in s:
            nodes.append(line)
        elif s.startswith('  ') and nodes:
            nodes[-1] += '\n' + line
        elif not s.startswith('  ') and s and not s.startswith('-'):
            break
processed = []
for n in nodes:
    if 'corp-proxy' not in n:
        n = n.rstrip()
        if n.endswith('}'):
            n = n[:-1] + ', dialer-proxy: corp-proxy}'
        processed.append(n)
insert = '\n'.join(processed)
cfg = cfg.replace(
    '  - {name: "corp-proxy", type: http, server: ' + "${ENTERPRISE_PROXY_IP}" + ', port: ' + "${ENTERPRISE_PROXY_PORT}" + '}',
    '  - {name: "corp-proxy", type: http, server: ' + "${ENTERPRISE_PROXY_IP}" + ', port: ' + "${ENTERPRISE_PROXY_PORT}" + '}\n' + insert
)
# DNS nameserver-policy
domains = "${INTERNAL_DOMAINS}"
dns1 = "${INTERNAL_DNS_1}"
dns2 = "${INTERNAL_DNS_2}"
if 'nameserver-policy' not in cfg and domains and dns1:
    cfg = cfg.replace('  fake-ip-range:', f'''
  nameserver-policy:
    "{domains}":
      - {dns1}
      - {dns2}
  fake-ip-range:''', 1)
with open("/etc/mihomo/config.yaml", 'w') as f:
    f.write(cfg)
print("完成")
PYEOF
fi

echo "配置已生成: ${OUTPUT_CONFIG}"
