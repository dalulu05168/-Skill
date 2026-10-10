---
name: script-qa
description: 对财经资料包和模拟群聊的事实、节奏、角色、媒体权限和发布状态作最终审稿。
---
# script-qa — 罗马尼亚金融内容准确性技能
## 最终审核顺序
先用`../bvb-fact-check/SKILL.md`审事实，必要时`../news-priority/SKILL.md`审事件，涉及模拟成员再用`../character-consistency/SKILL.md`审身份，最后执行此门禁。
## 硬性质量门禁
- **时段**：`Europe/Bucharest`时区+夏冬令时；`../romania-market-director/references/operating-standard-2026-10-09.md`的16节点为最高标准，当前仓库时段整体提前30分钟；备料/发布不能互换，未有正式收盘数据不能称收盘价。
- **数据与引证**：每个定量陈述有原文证据、时间、单位、涨跌基准；无法核实就`BLOCKED`或内部待核验稿，不能硬补。
- **内容**：新闻与股市影响有传导逻辑、对立解释与风险；重复新闻压缩但保留重大修订。审稿必须记录重要性和来源错误。
- **角色**：逐位身份四重核验；助理/教授出场时机、课程类型、65名角色语气/授权媒体和已采用记忆一致。
- **节奏**：工作日工作上午40—45条、下午约40条、晚上约45条是**大时段总量**且特殊情况可变，不是单节点凑数。时间写在栏目标题，不在人物每句话前标时刻；成员自然短句。
- **真实性**：模拟角色需明确标记“虚构教学模拟”；不冒充真实投资者，不编造持仓、收益、交易执行或专业资质。
- **发布授权**：只允许`DRAFT / REVIEW_REQUIRED / APPROVED / PUBLISHED`。后两者必须有人工审批凭据；创建文件、复制文案和提醒均不代表已发送。
## 输出报告
`time_gate,evidence_gate,news_gate,persona_gate,rhythm_gate,release_gate,status,missing_fields,next_action`。总状态只可`PASS_INTERNAL / NEEDS_REVIEW / BLOCKED`；只要硬性门禁失败即不可发布。
## 验证能力边界
可参考`../../third_party/orchestra-research/AI-Research-SKILLs/16-prompt-engineering/instructor/SKILL.md`的结构化输出和`../../third_party/orchestra-research/AI-Research-SKILLs/17-observability/phoenix/SKILL.md`的追踪方式；未安装服务或依赖就不能称已执行自动评测。
运行原回归：`python -m unittest discover -s .agents/skills/romania-stock-intelligence/tests -v`及`python skills/romania-market-director/scripts/validate_persona_roster.py`。

## 2026-10-10 七项反馈增量规则
必须读取 skills/romania-market-director/references/teaching-editorial-standard.md（仓库根目录相对路径）。该规则落实透明模拟、禁止吹捧接龙、周一三五课程链、延迟提问与助理答疑、热点证据、真实资质、每日执行单和单条单重点；保留16节点与65人身份，冲突的旧长话/课程说明以本次规则为准。结构检查不等于事实核验或发布批准。


## 人物情商与跨场记忆增强（2026-10-10）
交付前加载 `../romania-market-director/references/high-empathy-storycraft-v2.md`：禁止无证据往事、无故跑题、虚构业绩、催促投资、人身贬低与机械附和；有依据的沉默、不同意见和情绪共情允许保留。使用 `tools/storycraft_contract.py` 阻止引用不存在的正式场次/消息，用户明确批准之后方可采用。仅能标出规则化的错误和部分语言警告，自动审稿不等于外部事实核验或群发批准。
