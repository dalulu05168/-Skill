---
name: bvb-fact-check
description: 核实罗马尼亚BVB公告、价格指数、来源和时间，防止错误行情进入报告。
---
# bvb-fact-check — 罗马尼亚金融内容准确性技能
## 使用条件
用于每份BVB行情、新闻、盘中分析、尾盘观察与教授分析。先遵守 `../../.agents/skills/romania-stock-intelligence/SKILL.md` 中的数据真实性要求与 `../romania-market-director/references/operating-standard-2026-10-09.md` 的现行16节点（原时段均提前30分钟）。
## 必须执行
1. 区分新闻发布时间、发生时间、市场观测时间、网页抓取时间。时区用 `Europe/Bucharest`，包含DST，不用固定UTC偏移。
2. 每个数字单独记录代码/品种（BET≠BET-TR）、数值、币种与单位、比较基准、来源原文URL、观测时间、延迟状态和上一报告对比。缺少证据不得从其他时刻沿用。
3. 必须核对可访问的BVB公告、发行人公告、BNR/ECB等官方原始资料；媒体报道仅作为独立交叉佐证。成功解析RSS、Pydantic结构通过**不代表事实已核验**。
4. 检查涨跌幅的基准、%与百分点、收市阶段；17:45尾盘阶段不能写最终收盘价，来源500错误时标记`未获取`。
5. 将`事实/分析假设/情景`分开；讨论具体传导机制与可能反例，不能将相关性直接称为因果。
6. 核验状态：`VERIFIED`（逐项原始证据齐备）、`PARTIAL`（仍有缺项）、`BLOCKED`（重大事实冲突或无来源）；仅VERIFIED并经真人批准的字段可以进入正式稿。
## 交付
输出字段化证据台账，包含时间、来源、核实项与失败原因；无法核实必须写待核实，不捏造行情、不承诺收益、不代客下单。
## 可参考
`../../third_party/orchestra-research/AI-Research-SKILLs/16-prompt-engineering/instructor/references/validation.md` 与 `../../third_party/orchestra-research/AI-Research-SKILLs/20-ml-paper-writing/ml-paper-writing/references/citation-workflow.md`。学术引用流程不能直接当BVB行情接口。
