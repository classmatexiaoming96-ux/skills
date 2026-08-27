---
name: lark-archify
description: 将系统描述、代码证据或 Mermaid 转换为经过 Archify 校验的架构图、工作流、时序图、数据流或生命周期图，并发布为飞书可编辑白板；必要时附带外部交互 HTML。适用于技术方案、代码架构、PR 变化和运行链路可视化，不用于自由插画或无证据拓扑推断。
license: MIT
metadata:
  requires:
    bins: ["node", "lark-cli"]
    skills: ["archify"]
---

# Lark Archify

Archify 负责 Typed JSON、确定性校验和可信交付；官方 `lark-cli` 负责把通过校验的结果写入飞书文档或白板。不要用自由绘图替换 Archify 的事实与校验契约。

## 启动检查

1. 运行 `lark-cli --version`；缺失时停止并指向 <https://github.com/larksuite/cli>，不要静默安装。
2. 定位已安装的 Archify Skill 根目录，其中必须存在 `bin/archify.mjs`、`schemas/` 和 `examples/`。缺失时说明依赖，并建议用户安装 `tt-a1i/archify`；未经允许不要联网安装。
3. 默认使用 `--as user`。写入已有画板前必须确认目标 token；`--overwrite` 会整板重建，目标非空时必须得到明确确认。

## 生成可信图

### 1. 选择图类型

| 类型 | 适用问题 |
|---|---|
| `architecture` | 组件、服务、存储、基础设施和边界 |
| `workflow` | 审批、工具调用、Runbook、CI/CD 和分支 |
| `sequence` | API 调用、请求生命周期、异步消息和返回 |
| `dataflow` | 数据管线、血缘、PII、转换、存储和消费者 |
| `lifecycle` | 状态、事件、等待、重试、取消和终态 |

不确定时运行：

```bash
node <archify-root>/bin/archify.mjs guide '<场景>' --json
```

图反映真实代码时，先收集文件、符号、调用关系、配置和版本证据。找不到的关系标记为未知，不得凭常识补成“看起来合理”的拓扑。

### 2. 生成并校验 Typed JSON

只读取所选类型 schema、`common.schema.json` 和一个同类型示例。使用新稳定 ID 和当前领域语言，示例只提供字段形状。

先写候选 JSON，再校验：

```bash
node <archify-root>/bin/archify.mjs validate <type> ./diagram.json --quality showcase --json
```

默认一条明显主路径、短支路、稀疏标签，主要节点不超过 12 个。除非诊断要求，不预先添加 `via`、`channelX`、`channelY` 或 `labelAt`。

校验失败时只修改 `diagnostics[].subject` 指向的对象，并从 `supportedFixes` 中选择修复。连续两轮未降低最佳错误数时停止并如实报告，不整图盲改。

### 3. 交付 Archify HTML

```bash
node <archify-root>/bin/archify.mjs deliver <type> ./diagram.json ./diagram.html --quality showcase --json
node <archify-root>/bin/archify.mjs visual-check ./diagram.html --json
```

非零退出码不能描述为成功。`visual-check` 的自动回执仍是 `visualReview: pending`；只有实际检查截图后才能声称视觉验收。

## 选择飞书交付形态

默认选择 **可编辑白板**：从已交付 HTML 提取 canonical SVG，导入飞书白板。阅读 [飞书交付](references/lark-delivery.md) 后再写入。

- **可编辑白板**：默认；适合协作、评论和继续修改。
- **HTML5 Block**：仅当用户确实需要交互、单文件小于 500KB，并接受 iframe 内嵌；Archify 常见完整 HTML 会超过限制。
- **外部交互链接 + 飞书白板**：完整 HTML 超过 500KB 时的推荐组合。
- **静态图片**：只在用户不需要编辑或环境无法导入 SVG 时使用。

使用本 Skill 自带脚本提取 SVG：

```bash
node <this-skill>/scripts/extract-archify-svg.mjs ./diagram.html ./diagram.svg
```

脚本拒绝多个 SVG、脚本标签和远程资源引用；它只提取，不修改可信 HTML。

## 发布到飞书

### 插入现有文档并创建新白板

先读取文档大纲和目标章节，确认锚点后插入：

```bash
lark-cli docs +fetch --doc '<doc>' --scope outline --max-depth 3 --detail with-ids --as user
lark-cli docs +update --doc '<doc>' --command block_insert_after --block-id '<anchor>' --content '<whiteboard type="svg" path="@./diagram.svg"></whiteboard>' --revision-id '<revision>' --as user
```

### 更新已有白板

```bash
lark-cli whiteboard +update --whiteboard-token '<board_token>' --input_format svg --source @./diagram.svg --idempotent-token '<稳定的10字符以上token>' --overwrite --as user
```

同一次逻辑更新重试时复用同一个幂等 token。目标已有内容但用户未确认整板重建时，不添加 `--overwrite`，也不要假装追加能替代更新。

### 验证

```bash
lark-cli whiteboard +export --whiteboard-token '<board_token>' --output-type preview --output ./board-preview.png --as user
```

实际查看预览，核对节点、连线方向、标签、边界、文字可读性和是否出现解析降级；再回读文档确认白板位于正确章节。

## 完成标准

- JSON 事实与证据一致，没有编造拓扑。
- Archify showcase 校验通过，最终校验后未再修改 JSON。
- 飞书交付形态符合 500KB、可编辑性和交互需求。
- 写入后导出并检查画板预览，回读文档位置。
- 返回图类型、JSON/HTML/SVG 路径、验证回执摘要、飞书文档或白板链接，以及任何降级或未验证项。

## 上游

Archify：<https://github.com/tt-a1i/archify>；飞书执行层：<https://github.com/larksuite/cli>。两者均采用 MIT 许可。
