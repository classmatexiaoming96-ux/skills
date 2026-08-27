# Archify → 飞书交付

## SVG 预检

Archify 的 canonical SVG 仍需经过飞书白板语义检查：

- 必须有 `<svg>` 根节点和 `viewBox`。
- 文本应保留为 `<text>` / `<tspan>`，不要路径化。
- 远程图片、脚本、事件处理器和外部字体不得进入白板输入。
- 飞书可编辑元素包括常见形状、线、折线、路径、文本、分组、基础 transform、受支持阴影和渐变。
- `pattern`、`clipPath`、`mask`、非阴影 filter、复杂 gradient 可能降级或渲染异常。若出现诊断，优先对导出的飞书版 SVG 做局部兼容调整；不要改已经冻结的 Archify JSON/HTML。
- 调整后的飞书版 SVG 是派生产物，需单独记录，不得声称与 Archify canonical SVG 字节一致。

若本机已有 `@larksuite/whiteboard-cli`，可以在写入前做转换检查。需要通过 `npx -y` 下载时先取得用户许可：

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 -i ./diagram.svg --to openapi --format json -o ./diagram.openapi.json
```

## HTML5 Block 判断

只有同时满足以下条件才内嵌：

- 用户要求在飞书文档内直接交互。
- 完整单文件 HTML 小于 500KB。
- 根布局在约 820px 文档宽度下可读。
- `<head>` 含 viewport、`use-iframe=true`、明确的 `html-box-height-mode` 和描述。
- 不包含大 Base64 图片、字体、长数据或外部不可信脚本。

否则保留可编辑白板，并把完整 HTML 发布到用户认可的站点后插入链接。发布站点是额外外部写入，必须由用户明确授权。

## 写入安全

- 新建白板：在文档候选 XML 中插入 `<whiteboard type="svg" path="@./diagram.svg">`，或用 `block_insert_after`。
- 已有白板：先确认 token、现状和预期模式。
- `--overwrite` 会先删除已有画板全部内容；目标非空时必须明确确认。
- `--idempotent-token` 至少 10 字符；同一逻辑更新的所有重试复用同一值。
- 写入成功不等于视觉成功；必须 `whiteboard +export --output-type preview` 并实际检查。
