# 飞书发布契约

## 原生表达映射

| 信息关系 | 优先表达 |
|---|---|
| 结论、论证、连续说明 | 标题 + 段落 |
| 步骤、并列项、检查项 | 有序/无序列表、Checkbox |
| 精确字段比较或映射 | 表格 |
| 单个风险、限制或关键结论 | Callout |
| 流程、依赖、分支、时序、层级、因果、拓扑 | 白板 |
| 对象外观、界面、场景、证据截图 | 图片 |
| 代码、命令、配置 | 代码块 |
| 必须由读者操作或探索的内容 | HTML5 Block |

避免把所有内容做成卡片，也不要为了“丰富”强行插图。

## Presentation Decision

创建草稿前提交完整 JSON。只把确实需要最低数量保证的 `whiteboard`、`img`、`html5-block` 写入 `blocks`：

```json
{
  "audience": "目标读者",
  "reader_task": "读完后要完成的判断或行动",
  "genre_contract": "explainer",
  "adapter": null,
  "presentation_mode": "normal",
  "visual_plan": {
    "reason": "为什么这些视觉块能降低理解成本",
    "blocks": [
      {"type": "whiteboard", "min_count": 1, "purpose": "展示主要流程"}
    ]
  }
}
```

`presentation_mode`：

- `formal`：正式克制，只保留体裁必要结构。
- `normal`：视觉块只在降低理解或执行成本时出现。
- `rich`：主动使用飞书组件，但每个组件必须说明用途。

## 发布前检查

- 标题层级连续，术语和编号体系一致。
- 首屏能回答“这是什么、为什么值得读、读者会得到什么”。
- 每节有明确任务，段落与视觉相邻。
- 表格用于精确比较，白板用于关系，图片用于视觉证据。
- XML 资源使用任务目录内的 `@./relative-path`。
- HTML5 Block 是完整单文件，含 viewport meta，不内联大图、字体或长数据，总长度不超过 500KB。
- 任何公开图片 URL 都是可信 HTTPS；拒绝私网、loopback、link-local 及可疑重定向。
- 创建或更新完成后回读，检查 warnings、降级与资源缺失。
