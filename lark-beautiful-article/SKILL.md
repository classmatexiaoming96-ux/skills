---
name: lark-beautiful-article
description: 将网页、PDF、DOCX、Markdown、纯文本或零散材料编辑成结构清晰、视觉克制的飞书原生文章，并安全地创建或精确更新飞书文档。适用于长文、报告、教程、解释文、复盘、方案和 briefing；不用于普通网页、后台或通用应用开发。
license: MIT
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark Beautiful Article

把来源材料转化为可协作、可继续编辑的飞书原生文档。正文优先使用飞书标题、段落、列表、表格、Callout、图片和白板；只有原生块不能表达必要交互时才使用 HTML5 Block。

## 启动检查

1. 运行 `lark-cli --version`。若不可用，停止并给出官方项目 <https://github.com/larksuite/cli>，不要静默安装。
2. 默认显式使用 `--as user`。遇到认证或 scope 错误时按 CLI 提示修复；不要反复重试同一参数。
3. 如果运行环境也安装了官方 `lark-doc` Skill，先加载它以取得当前版本的 XML、认证和命令约束；本 Skill 负责编辑编排，不取代官方底层协议。

## 路由

- **新建文章**：执行“来源 → 编辑方案 → 候选稿 → 创建 → 回读”。
- **改写现有飞书文档**：执行“回读 → 局部计划 → 精确 patch → 回读”；除非用户明确要求全文重建，不使用 `overwrite`。
- **原样导入完整 Markdown/DOCX**：优先走 `lark-cli drive +import`，不执行本 Skill 的编辑重构。
- 用户真正要的是网页应用、Dashboard 或交互产品时，不进入本 Skill。

## 新建文章工作流

### 1. 建立事实底座

将输入统一为可引用的 Markdown 或纯文本，并保存来源清单：来源名称、URL/文件路径、抓取或读取时间、语言、抽取缺口、低置信内容。不得用流畅改写掩盖抽取失败。

默认保留全部事实。先阅读 [文章契约](references/article-contracts.md)，再根据用户任务选择文章类型和建议保留比例；用户指定的比例优先。

### 2. 形成编辑方案

在写正文前形成一个紧凑方案，至少包括：

- 目标读者和阅读任务
- 文章类型、信息保留比例、必须保留和可删减内容
- 一句话主张和章节大纲
- 语气、目标语言、版式密度
- 表格、图片、白板、代码、Callout 或 HTML5 Block 的用途
- 封面策略与素材缺口

若用户尚未决定且选择会明显改变成品，分别确认文章类型、视觉基调、信息密度、配图模式和封面。可以推荐，但不能把推荐当成用户已经选择。用户已明确给出的决定不要重复询问。

### 3. 生成飞书原生候选稿

阅读 [飞书发布契约](references/lark-publication.md)，优先生成 XML 候选稿。遵循：

- 结论先行，按读者任务组织，不按来源顺序机械搬运。
- 每个视觉块必须承担比较、解释、证据、导航或行动功能。
- 原始事实、数值、限定条件、代码和引用不得因排版被改变。
- 图片使用可信公开 HTTPS URL 或任务目录内的相对文件。
- 架构、流程、依赖、时序等关系优先用飞书白板；简单并列继续用列表或表格。
- HTML5 Block 仅用于必要交互，必须是单文件、总长度不超过 500KB、文档宽度约 820px 下可读。

### 4. 本地预检

初始化独占草稿目录并生成候选稿：

```bash
lark-cli docs +script --command init-draft --presentation-decision '<完整 JSON>' --format json
lark-cli docs +script --command parse --content "@./<draft_path>" --format json
```

以 `data.assessment.status` 和 `data.diagnostics[]` 为准；只修复诊断指向的局部问题。用户要求预览或方案尚未确认时，到此停止，不写入飞书。

### 5. 创建并回读

用户已明确要求创建文档后执行：

```bash
lark-cli docs +create --doc-format xml --content "@./<draft_path>" --as user
lark-cli docs +fetch --doc '<返回的文档 URL 或 token>' --detail with-ids --as user
```

检查 `ok`、`warnings`、`tips`、`revision_id`、缺失资源及降级块。创建成功后的局部问题必须在同一文档内修复，不得再新建一份替代品。

封面是独立资源，只有用户选择封面且已有素材时再执行：

```bash
lark-cli docs +resource-update --doc '<doc>' --type cover --file ./cover.png --as user
```

## 更新现有文档

1. 先读取最小必要范围；编辑时使用 `--detail full` 或 `with-ids`。
2. 记录当前 `revision_id`、目标 block ID、必须保留的图片/白板/引用 token 和评论上下文。
3. 将改动拆成最小操作：`str_replace`、`block_replace`、`block_insert_after`、`block_delete` 或 `block_move_after`。
4. 写入时传入已观察到的 `--revision-id`；冲突后重新 fetch，不沿用旧 block ID。
5. 每轮写入后回读受影响章节。验证事实、结构、资源块和用户要求，而不只检查命令退出码。

示例：

```bash
lark-cli docs +fetch --doc '<doc>' --scope outline --max-depth 3 --detail with-ids --as user
lark-cli docs +fetch --doc '<doc>' --scope section --start-block-id '<heading_id>' --detail full --as user
lark-cli docs +update --doc '<doc>' --command block_replace --block-id '<block_id>' --content '<p>...</p>' --revision-id '<revision>' --as user
```

不要用 `overwrite` 处理普通润色或章节重写；它可能丢失评论和暂不支持的资源。

## 完成标准

- 来源缺口和推断已明确标记。
- 信息保留比例、文章结构和视觉策略符合已确认方案。
- 本地候选稿通过解析；服务端写入无未解释 warning。
- 新建后已回读，更新后已回读受影响范围。
- 返回文档 URL、文章类型、信息保留策略、主要视觉块以及仍未关闭的缺口。

## 上游

编辑思想参考 Garden Skills 的 `beautiful-article`；飞书执行契约以官方 <https://github.com/larksuite/cli> 当前版本为准。两者均采用 MIT 许可。
