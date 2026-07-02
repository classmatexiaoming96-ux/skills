#!/bin/bash
# ============================================================
# start.sh — 启动 Mihomo 代理服务
# ============================================================
set -euo pipefail

CONFIG_ENV="/etc/mihomo/env.sh"
CONFIG_FILE="/etc/mihomo/config.yaml"
MIHOMO_BIN="/usr/local/bin/mihomo"

if [ ! -f "$CONFIG_ENV" ]; then
    echo "请先配置 /etc/mihomo/env.sh"
    exit 1
fi
source "$CONFIG_ENV"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "先运行 configure.sh"
    exit 1
fi

if [ ! -f "$MIHOMO_BIN" ]; then
    echo "下载 mihomo 到 /usr/local/bin/mihomo"
    exit 1
fi

chmod +x "$MIHOMO_BIN"

echo "检查 GeoIP 数据略..."

echo "验证配置..."
if ! "$MIHOMO_BIN" -t -d /etc/mihomo 2>&1; then
    echo "配置验证失败"
    exit 1
fi

echo "停止旧实例..."
pkill mihomo 2>/dev/null || true
sleep 1

echo "启动 Mihomo..."
nohup "$MIHOMO_BIN" -d /etc/mihomo > /tmp/mihomo.log 2>&1 &
sleep 2

if pgrep -x mihomo > /dev/null; then
    echo "Mihomo 已启动 PID: $(pgrep -x mihomo)"
    echo "HTTP 代理: 127.0.0.1:${MIHOMO_HTTP_PORT:-7890}"
else
    echo "启动失败, 查看日志 tail -30 /tmp/mihomo.log"
    exit 1
fi

echo "注册 systemd 服务..."
mkdir -p /etc/systemd/system
cat > /etc/systemd/system/mihomo.service << 'SERVICEEOF'
[Unit]
Description=Mihomo Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -d /etc/mihomo
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF
systemctl daemon-reload 2>/dev/null || true
systemctl enable --now mihomo 2>/dev/null || true
echo "完成"
