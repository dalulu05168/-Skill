# P004 新导演端到端工作流（免费离线的任务编排和检查）

## 当前实现与边界

**已经是代码而非只有口头方案：**

- `scripts/director_cast.py`：根据主题、兴趣、职业、时段与近期出场情况挑选候选人物，返回具体选角理由。候选人物可沉默，不要求全部开口。
- `scripts/director_workflow.py`：`prepare` 生成完整的AI编剧任务与严格的JSON交付约定；`review` 检查返回对白中的角色授权、时间、课程类型、当场引用、正式历史引用与模块二虚构交易引用；失败返回明确退稿理由。
- `scripts/approve_scene.py`：`finalize` 在**编辑确认和操作方明确采用**、人物已在新正式名册中的情况下，才把合格的虚构场次写进本故事独立SQLite数据库；重复采用幂等，不允许覆盖已存历史。
- `scripts/scene_memory.py`：仅存**正式采用的本故事**场次与人物台词，可按编号与关键词检索，真实交易记录仍属于模块二，不能由编剧创建。
- `tests/test_director_workflow.py` 与 `tests/test_approve_scene.py`：测试候选65人的批量选角、越权角色、教授时间、假新闻/交易、无法定位的历史、退稿以及双重确认记忆写入。

**未实现/不应误称完成：** 未连接免费或付费大模型API；`prepare` 只给一份可复制给AI的任务包，必须由可用AI生成JSON后再送回 `review`。因此不等于AI已经自动写出大量高质量对白。没有自动刷新实盘行情、没有交易模块二实际成交接口、没有WhatsApp自动转发或发布。尚未确认的新65名档案只供**沙盒排演**使用，正式名册保持空白。测试中创建的临时“已确认名册”不会写到GitHub。

## 用法：第一阶段免费半自动

在仓库根目录执行：

```bash
python skills/p004-fiction-director/scripts/director_workflow.py prepare \
  --request skills/p004-fiction-director/examples/workflow-request-energy.json > /tmp/p004-task.json
```

复制任务中的 `llm_prompt` 给现有AI模型，将其返回的**JSON对象**保存为 `/tmp/p004-draft.json`，然后核验：

```bash
python skills/p004-fiction-director/scripts/director_workflow.py review \
  --package /tmp/p004-task.json --manuscript /tmp/p004-draft.json
```

返回 `BLOCKED_REWRITE_REQUIRED` 时必须根据 `rewrite_instruction` 返工；返回 `EDITORIAL_REVIEW_REQUIRED` 只代表结构性阻断通过，**仍不能表示新闻核实完毕、地道罗语合格或准许发布**。

正式采用（本次绝不能运行，因为新的 `characters/approved-roster.json` 仍为空）需要另外确认人物名单、完成实质审稿，并且明确执行：

```bash
python skills/p004-fiction-director/scripts/approve_scene.py \
  --package /tmp/p004-task.json --manuscript /tmp/p004-draft.json \
  --db /persistent-path/p004-scenes.sqlite3 \
  --approved-roster skills/p004-fiction-director/characters/approved-roster.json \
  --editorial-confirmed --operator-confirmed
```

数据库文件应放在受备份保护的持久磁盘，而不是无持久化的临时云容器；具体流程暂未接入用户网页，示例中的命令属于开发者手动阶段。

## 强制安全约束

导演最高指挥权是**剧情调度权**，用户临时插播写入 `director_override`；不授予通过虚构人物冒充真人、编造真实交易/持仓、跳过对最新新闻的事实核验或改写已确认历史的权限。

一条实际发生过的剧情需要本故事已确认 `scene_id` / `message_id` / `speaker_id` 三元组作证。候选人第一次登场只能根据人设说话，不可以凭空引用昨天/上周“曾经买入股票、得到收益或和谁吵架”。

模块二与四的真实联动另行开发；当前发现虚构交易引用时，先阻断，绝不将其当成模块二真实成交。

## 验收与下一步

```bash
python -m unittest discover -s skills/p004-fiction-director/tests -p 'test_*.py' -v
```

此流程验证确定性结构逻辑，不验证罗马尼亚文化口语、文学感染力、真实财经数据或大量模型生成语句差异。下一阶段需接入用户选择的可用AI运行器、财经数据证据包、模块二只读已成交账本，并运行真实的65角色多日生成、重写与回归评估。所有这些事项尚未宣称验收通过。
