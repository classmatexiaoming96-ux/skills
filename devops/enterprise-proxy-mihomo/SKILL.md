---
name: enterprise-proxy-mihomo
description: 开箱即用的企业代理搭建 — Mihomo + 内部网络隧道。适配任何通过 HTTP 正向代理出外网的企业环境。配置占位符替换公司 IP/DNS/域名即可部署。
tags:
  - mihomo
  - proxy
  - enterprise
  - forward-proxy
  - vpn
  - tunnel
---

# Enterprise Proxy via Mihomo

> 在受企业防火墙限制的开发机上，通过 **Mihomo + 企业正向代理隧道** 访问外网的
> 完整方案。适用于任何：\
> • 开发机只能通过企业内部 HTTP 代理出外网\
> • 需要 AI API 调用、npm 安装、git clone 等外网操作\
> • 企业代理出口 IP 是数据中心的（被 API 限流/封禁），需要住宅出口 IP

## 架构

```
外部 API (Anthropic/OpenAI/GitHub)
  ↑ tunnel (经 EqualCDN 或其他 VPN 供应商节点)
Mihomo (本地代理服务器 :7890)
  ↑ dialer-proxy
企业 HTTP 正向代理 (10.x.x.x:PORT)
  ↑
开发机上的所有 CLI 工具
  - Claude Code  → wrapper 脚本 → 127.0.0.1:7890
  - OpenAI Codex → wrapper 脚本 → 企业代理:端口
  - curl/npm/git → 配置 env 变量 → 127.0.0.1:7890
```

## 前置依赖

```bash
# 1. Mihomo 二进制 (v1.19.2+)
#    从 https://github.com/MetaCubeX/mihomo/releases 下载
curl -L -o /usr/local/bin/mihomo https://github.com/MetaCubeX/mihomo/releases/download/v1.19.3/mihomo-linux-amd64-v1.19.3.gz
gunzip -f /usr/local/bin/mihomo.gz 2>/dev/null || true
chmod +x /usr/local/bin/mihomo

# 2. 企业正向代理地址（IP:端口）
#    询问你的 IT 部门，或从浏览器代理设置中获取

# 3. 外部 VPN 订阅链接（可选，仅当需要出口 IP 不是企业 IP 时需要）
#    可选供应商：EqualCDN / Fastly / Shadowsocks 等
```

## 配置抽象

本 skill 所有公司的具体信息集中在 **一个地方**，修改后写为
`/etc/mihomo/env.sh`，其他脚本自动读取：

```bash
# /etc/mihomo/env.sh  —  所有公司特定配置在此
# ============================================

# 企业 HTTP 正向代理（⚠️ 必须用 IP，不能用域名，见下文）
ENTERPRISE_PROXY_IP="10.x.x.x"
ENTERPRISE_PROXY_PORT="8118"

# 内部 DNS 服务器（从 /etc/resolv.conf 获取）
INTERNAL_DNS_1="10.x.x.x"
INTERNAL_DNS_2="10.x.x.x"

# 内网域名后缀列表（以逗号分隔）
INTERNAL_DOMAINS="+.example.com,+.corp.net,+.internal.io"

# Web 控制面板密钥
WEB_UI_SECRET="your-secret-here"

# Mihomo 监听端口
MIHOMO_HTTP_PORT="7890"
MIHOMO_SOCKS_PORT="7891"
MIHOMO_API_PORT="9090"
MIHOMO_API_PORT="9090"
```

## 快速部署

```bash
# 1. 创建配置目录
mkdir -p /etc/mihomo/ui /etc/mihomo/scripts

# 2. 设置 env.sh（编辑上面占位符）
cp /root/.hermes/skills/devops/enterprise-proxy-mihomo/templates/env.sh.template \
  /etc/mihomo/env.sh
vim /etc/mihomo/env.sh   # 填入公司实际值

# 3. 运行配网脚本（从 env.sh 读取配置，生成 config.yaml）
bash /root/.hermes/skills/devops/enterprise-proxy-mihomo/scripts/configure.sh

# 4. 启动
bash /root/.hermes/skills/devops/enterprise-proxy-mihomo/scripts/start.sh

# 5. 验证
bash /root/.hermes/skills/devops/enterprise-proxy-mihomo/scripts/verify.sh
```

## 为 CLI 工具配置代理

### Claude Code → 走 Mihomo

创建 wrapper 脚本 `/usr/local/bin/claude-wrapper.sh`：

```bash
#!/bin/bash
# Claude Code wrapper - 强制走 Mihomo 代理
exec env \
  http_proxy=http://127.0.0.1:${MIHOMO_HTTP_PORT:-7890} \
  https_proxy=http://127.0.0.1:${MIHOMO_HTTP_PORT:-7890} \
  HTTP_PROXY=http://127.0.0.1:${MIHOMO_HTTP_PORT:-7890} \
  HTTPS_PROXY=http://127.0.0.1:${MIHOMO_HTTP_PORT:-7890} \
  NO_PROXY=localhost,127.0.0.1,${INTERNAL_DOMAINS//+/} \
  no_proxy=localhost,127.0.0.1,${INTERNAL_DOMAINS//+/} \
  /usr/bin/claude "$@"
```

### OpenAI Codex → 走企业代理直连

```bash
#!/bin/bash
# Codex wrapper - 直接走企业代理（不用 VPN），减少延迟
HTTP_PROXY="http://${ENTERPRISE_PROXY_IP}:${ENTERPRISE_PROXY_PORT}" \
HTTPS_PROXY="http://${ENTERPRISE_PROXY_IP}:${ENTERPRISE_PROXY_PORT}" \
exec /usr/lib/node_modules/@openai/codex/bin/codex.js "$@"
```

### 通用验证命令

```bash
# 检查出口 IP（如果走 VPN 隧道，应显示住宅 IP）
curl -s -x http://127.0.0.1:${MIHOMO_HTTP_PORT:-7890} https://httpbin.org/ip

# 检查进程代理环境变量
cat /proc/<pid>/environ | tr '\0' '\n' | grep proxy

# 检查 TCP 连接方向
ss -tp | grep <pid>
```

## 关键坑点

### ⚠️ 企业代理必须用 IP 不能用域名

Mihomo 在 fake-ip 模式下会拦截所有 DNS 解析。如果企业代理用域名设置，
该域名也会被 fake-ip 拦截导致无法解析。

**错误**：
```yaml
proxies:
  - {name: "corp-proxy", type: http, server: proxy.corp.com, port: 8118}
```

**正确**：
```yaml
proxies:
  - {name: "corp-proxy", type: http, server: 10.x.x.x, port: 8118}
```

### ⚠️ 所有 VPN 节点必须加 dialer-proxy

如果开发机无法直连外网，必须通过企业代理隧道。给每个 VPN 节点添加
`dialer-proxy: corp-proxy`，这样 Mihomo 会先连接企业代理，再通过
企业代理连接 VPN 节点。

### ⚠️ 内网域名 nameserver-policy 必须配置

内网域名不能由 fake-ip 拦截，必须在 `nameserver-policy` 中指定公司
内网 DNS：

```yaml
dns:
  nameserver-policy:
    "+.example.com,+.corp.net":
      - 10.x.x.x
      - 10.y.y.y
```

### ⚠️ Claude Code 是原生二进制

Claude Code 是 Go/Rust 原生 ELF 二进制（不是 Node.js 应用）。它
**不从 settings.json 读取 HTTP_PROXY**，直接从父进程继承环境变量。
`exec env` 方式比 `export` + `exec` 更可靠——能覆盖 .bashrc 等
所有 shell 启动脚本的代理值。

### ⚠️ 订阅链接获取可能无需代理

某些 VPN 订阅链接可以从开发机直连获取，不需要走企业代理（因为
企业代理出口 IP 是数据中心而非住宅，可能触发反爬）。尝试时不设
代理：

```bash
curl -sSL "https://subscribe-provider.example.com/link"
```

如果失败，再试企业代理：
```bash
http_proxy=http://${ENTERPRISE_PROXY_IP}:${ENTERPRISE_PROXY_PORT} \
  curl -sSL "https://subscribe-provider.example.com/link"
```

## 故障排查

| 症状 | 可能原因 | 修复 |
|---|---|---|
| Mihomo 启动后代理不通 | dialer-proxy 没设置 | 检查 config.yaml 每节点都有 `dialer-proxy: corp-proxy` |
| 内网页面打不开 | nameserver-policy 缺内网域名 | 在 DNS 段加入内网域名后缀 |
| Claude Code 还是直连 | wrapper 脚本没接管 | 检查 `which claude` 指向 wrapper |
| Codex 卡在 reconnecting | proxy wrapper 断了 | 检查 `/usr/bin/codex` symlink |
| VPN 节点连不上 | 企业代理域名解析被 fake-ip 拦截 | 在 env.sh 确保企业代理用 IP |
| 出口 IP 是数据中心 | 没走 VPN 节点 | 加 dialer-proxy + 检查 proxy-groups |

## 文件清单

| 文件 | 说明 |
|------|------|
| `/etc/mihomo/env.sh` | 公司特定配置（唯一需手动填写） |
| `/etc/mihomo/config.yaml` | Mihomo 配置（由 configure.sh 生成） |
| `/etc/mihomo/ui/` | Web 管理面板 |
| `/etc/mihomo/subscription_url` | VPN 订阅链接（chmod 600） |
| `/etc/systemd/system/mihomo.service` | systemd service |
| `/usr/local/bin/mihomo` | Mihomo 二进制 |
| `/usr/local/bin/claude-wrapper.sh` | Claude Code wrapper |
| `/usr/local/bin/codex-wrapper.sh` | Codex wrapper |
