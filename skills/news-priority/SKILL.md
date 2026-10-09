---
name: news-priority
description: 跨媒体新闻事件去重与重要程度分级，服务固定16节点和重大新闻人工提醒。
---
# news-priority — 罗马尼亚金融内容准确性技能
## 范围
在`../bvb-fact-check/SKILL.md`完成核查后，为16节点资料包和突发资讯候审队列分流；现有采集脚本`.agents/skills/romania-stock-intelligence/scripts/rss_intake.py`应保留，本Skill不是抓取器。
## 候选事件字段
保存`source_id, source_url, article_url, headline_original, language, published_at, updated_at, first_seen_at, issuer, ticker, event_type, factual_summary, event_key, source_hash, verification_status, material_revision`。缺失使用null，不能伪造日期、证券简称或译文。
## 去重和实质更新
1. RSS GUID、标准化URL与内容哈希处理单源重复；同GUID文本有改变时标记修订，重新候审。
2. 跨来源先按实体、市场、事件时间、事实三元组聚集，再通过文字相似度/多语言模型产生候选；不能只凭相似标题删除独立事件。
3. 核对主体、公告金额、行动、有效日期；新决定、撤回、金额改变是实质进展，应保留并显示版本关系。
## 采集与候审状态接口（已实现的底座）
- RSS采集脚本的 `--state` v2 包含已观察摘要 `entries` 和每个 `item_id+digest` 对应的待人工审阅版本 `pending`。再次出现的旧新闻仍待审核，除非显式确认移出；同一GUID连续修订不能覆盖旧版本。
- 内容摘要包含标准化的官方文章URL；真实URL变化必须重新候审。旧v1状态曾见条目在迁移时按 `legacy_unreviewed` 候审，不能假定已审核。
- `--ack-file` 必须仅用于核对过候审版本标识后的人工作业确认；它不等同于 `VERIFIED`、新闻批准、群推送授权。审核证据与事实核验结果单独管理。
- `urgency_hint` 仅用于优先排列人工核实任务；在原文核查和人工判断之前，不能擅自升级为已确认的P0/P1，也不能触发向成员的消息。
- 不得把单次RSS抓取成功、结构测试或人工确认移出待办误称为已上线的自动监测服务。详细运行和迁移规范见 `../../docs/NEWS-OPERATIONS-2026-10-09.md`。

## 重要性判断
`P0`重大可能影响交易或系统事件→立即通知**人工审阅**；`P1`重要发行人/行业/官方宏观数据→进入最近对应节点；`P2`观点/旧闻/低相关性→归档。优先级必须写理由、证据、影响范围和不确定性。关键词分数不是价格预测或核验。
初次导入旧新闻只建立基线，不集中触发历史事件报警。采集源不可用时显示失败，不输出“暂无重大新闻”的假结论。
## 时间、授权
按 `../romania-market-director/references/operating-standard-2026-10-09.md` 权威16节点匹配；旧08/13/18独立简报不能覆盖。未经人工核实与批准不对群组发布、发送WhatsApp或推送交易指令。
## 开源参考
`../../third_party/orchestra-research/AI-Research-SKILLs/15-rag/sentence-transformers/SKILL.md`、`../../third_party/orchestra-research/AI-Research-SKILLs/15-rag/sentence-transformers/references/models.md`。多语言模型须用罗语/英语/中文样本测试误合并、漏合并，未装模型不声称已实现跨语言去重。
