# 飞书知识检索协议

## 自然语言映射

| 用户意图 | 首选动作 |
|---|---|
| 找包含某主题的资料 | `drive +search --query '<实体 主题>'` |
| 只找标题 | 加 `--only-title` |
| 最近我编辑过 | `--edited-since <范围>` |
| 我最初创建 | `--created-by-me` |
| 我目前 owner | `--mine` |
| 限定文档类型 | `--doc-types docx,wiki,...` |
| 限定 Wiki 空间 | `--space-ids <space_id>` |
| 限定云盘文件夹 | `--folder-tokens <folder_token>` |
| 已知章节名 | `docs +fetch --scope outline` 后转 `section` |
| 已知术语、错误码 | `docs +fetch --scope keyword` |
| 已知精确 block 范围 | `docs +fetch --scope range` |

“上个月”“本月”“今年 3 月”等日历表达应计算绝对日期边界，不要近似成固定 30 天；`1m` 在 CLI 中是 30 天。

## 候选台账模板

```text
- title:
  url_or_token:
  type:
  scope:
  matched_by:
  section_or_block:
  evidence:
  supports:
  conflicts:
  confidence:
```

台账是内部工作记录，不要求完整展示给用户，但最终答案的每个关键结论必须能映射到其中至少一项。

## 充分证据判断

满足以下条件通常可以停止检索：

- 直接事实由至少一个权威、相关且足够新的内部文档支持。
- 比较或归纳覆盖了用户指定的全部对象和时间范围。
- 数值包含口径、单位、时间和来源。
- 流程说明包含触发条件、主要步骤、异常或边界。
- 冲突来源已说明版本或适用范围，无法解释时不强行合并。

## 回答结构

1. 直接结论。
2. 关键依据，按重要性而非搜索顺序组织。
3. 来源链接和章节位置。
4. 冲突、缺口与置信度。

用户要求原始结果时返回紧凑的真实字段，不用摘要替代原始数据；仍应避免泄露无关敏感字段。
