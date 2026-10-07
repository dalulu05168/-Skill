# Romania Stock Intelligence V2.0 — Codex 可执行扩展

**版本**：2.0.0 | **运行**：Python 3.11+，仅标准库 | **位置**：`.agents/skills/romania-stock-intelligence/`

本版是在 V1.0 上*增量*实现的五个本地可执行功能。原先的 `scripts/validate_report.py`、`schemas/report.schema.json`、16节课程、三档日报模板、来源目录、其他技能/人物资料均不删除、不改写。Codex 可读取 `SKILL.md` 后按需执行 `python scripts/rsi_v2.py`。**所有数字依赖真实输入；本包不会自动获取交易所收费行情、联网抓取 BVB 报价、投递通知或创建定时任务。**

## 五个执行模块

| 命令 | 功能 | 可审计输出 | 限制 |
|---|---|---|---|
| `audit` | 数值/来源/时区/延迟校验，15分钟可比时间窗、跨来源和同源冲突 | `gate` + `findings` + 具体字段路径 | 仅核查元数据和一致性，无法证明网页实际显示该数值 |
| `bet` | BET 成分股加权贡献、涨跌广度、正负贡献、集中度 | `observed_subset_contribution_pp`、覆盖率、估计指数变动 | 并非交易所正式归因；缺部分权重不输出完整 BET 回报 |
| `events` | 来源可追溯的事件雷达、审查优先级、SQLite 去重 | `new/revised/unchanged` + 分数构成 | 优先级不是预测或市场冲击程度 |
| `store` / `compare` | SQLite 持久化已校验日报和历史比较 | SHA256、防覆盖、真实前份报告、绝对值差异 | 仅存用户实际录入/执行生成的报告；无历史就明确标记 |
| `professor` | 用证据、因果路径、反面观点与3种情景生成教授课程 | Markdown 课堂讲解 | 非语言模型独立验证，严格依赖输入事实和机制 |

## 开始执行（在仓库根目录）

```bash
cd .agents/skills/romania-stock-intelligence
python scripts/rsi_v2.py audit examples/v2/observations.synthetic.json --out /tmp/audit.json
python scripts/rsi_v2.py bet examples/v2/bet.synthetic.json --out /tmp/bet.json
python scripts/rsi_v2.py events examples/v2/events.synthetic.json --db /tmp/rsi-history.sqlite --out /tmp/events.json
python scripts/rsi_v2.py store tests/minimal_valid.json --db /tmp/rsi-history.sqlite
python scripts/rsi_v2.py compare tests/minimal_valid.json --db /tmp/rsi-history.sqlite
python scripts/rsi_v2.py professor examples/v2/professor.synthetic.json --out /tmp/professor.md
python -m unittest discover -s tests -v
```

Windows PowerShell：`python scripts/rsi_v2.py ...`，把 `/tmp/` 改为 `./output/`，该目录默认不提交；`--out` 会自动创建父目录。数据存储不应放在公开 Git 仓库，建议在服务器受控目录或本机用户数据文件夹。

注意：`examples/v2/*.synthetic.json` 是**虚构样例数据**，从不代表真实交易所观测；请勿复制到正式财经报告。V1 的 `tests/minimal_valid.json` 也只是一份“无行情、说明缺口”的测试报告。

## 正式数据输入与证据合同

1. **获取数据**：通过人工可追溯的 BVB/BNR/ECB 官方网页记录、官方文件或经过授权的可编程行情提供商取得时间点数据；不得无授权绕过站点反爬、实时授权或数据许可。
2. **填入** `observations` 记录：`instrument`、`value`、`unit`、`observed_at`（ISO 8601 时区偏移）、`timezone`（IANA）、`source_id`（必须在 `config/source-registry.json` 中）、`source_url`（具体页）、`evidence_locator`（页面栏目、表格行、公告号）、`delay_status`、`status`。标 `publisher_observed` 仅意味着操作者声称从发布方获取；程序不把它当独立校验证书。
3. **审查** `audit`：只要 `gate=fail`，不允许以已核实数据发布。`pass` 是数据合同通过，仍需要人/服务验证原始报价和许可；`pass_with_warnings` 需要逐项处置。
4. **BET 归因**：独立输入当前有效全量成分名单、*上一收盘时点*权重及同一计算区间的个股总价格变动。仅 `complete_roster=true` 且权重合计在 99.5%~100.5% 才生成 `estimated_total_return_pct`，并始终标**估计**。ETF 价格、BET-TR 股息再投资与 BET 价格指数不得混用。BVB 方法论含自由流通权重、权重调整及公司行动处理，故加权收益不是官方指数公式的替代。
5. **事件雷达**：输入原始事件发布日期、来源、证据位置、主题、罗马尼亚相关性标签和“可能的传导路径”。评分 `min(2×关联标签数,6) + 最近24小时3分/72小时1分 + 新增或修订2分`，只能表示**人工审查顺序**，不可表现为可靠性评分、涨跌概率或盈利预测。
6. **历史比较**：`store` 先调用原有 V1 报告校验器，通过后才写 SQLite。`report_id` 相同而内容变化会被拒绝，避免悄悄篡改历史；对于真正修订应制定单独的版本/修订链。`compare` 按相同指标名和单位比对之前**确实存入**数据库的上一份报告，缺失则报告不可比。
7. **教授课程**：输入事实须带原始 URL、时点、证据位置；同时至少有机制、反面解释、三种条件情景、核验点，欠缺任何一项直接报错。生成的是证据引导的教学框架，并不声称自动核实资料。

## 输出/错误与部署约束

- CLI `0`：处理成功；其中 `audit` 的 `pass_with_warnings` 仍返回 0，调用方应检查 `gate`。
- CLI `1`：`audit.gate=fail`（数据不可直接发布）。
- CLI `2`：输入解析失败、数据结构或来源不合规等。
- `events --db` 和 `store --db` 才会创建数据库；`compare` 用同一数据库路径并读取数据。
- 历史记录存在**本地 SQLite 文件**，不会在 Codex/ChatGPT 不同会话间自动同步，除非将数据库挂载在可靠的持久卷上。多机器生产运行请考虑 PostgreSQL 和备份/权限管理。
- `config/schedule.json` 仍是 **Europe/Bucharest 08:00、13:00、18:00 的规则，不是已激活的计划任务**。要真正定时执行需经用户许可单独部署运行器或任务。
- 不向 WhatsApp 直接发送讯息；研究观点不得包装成真实投资者回报或虚构人设互动。

## 推荐的 Codex 操作语句

> `$romania-stock-intelligence 请先阅读 SKILL.md 和 V2-README.md。对于给定的经许可的金融数据文件，执行 audit、BET 贡献、事件雷达、历史对比，再编写教授课程。若缺行情或证据，明确列出缺项，绝对不凭空补数字；不要自行开启定时任务。`

## 验收（真实功能）

- [x] 标准库直接运行；无需网络、pip 或外部 API Key
- [x] 质量闸门：缺来源、未来时间、错误时区、跨来源和同来源冲突
- [x] BET 估算、涨跌广度、权重覆盖率；不完整禁止输出全指数收益
- [x] 事件去重及修订识别，非法批次禁止部分写入
- [x] 历史报告 SHA256、幂等、防无声覆盖、夏/冬令时排序
- [x] 教授内容必须有事实证据、机制、反证、条件情景
- [x] V1 回归测试继续运行
- [ ] 实时行情付费授权、BVB/第三方 API 接入（没有凭空声称已接入）
- [ ] 定时任务和 ChatGPT 通知服务实际运行（没有未经许可创建）
- [ ] 生产规模高可用存储、备份与独立来源证据抓取

## 官方参考

- BVB BET 计算方法：<https://bvb.ro/info/indices/2025/BVB-EN_Manual-BET_V_01-2022.pdf>
- BVB BET 市场页面：<https://bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx?i=BET_>
- 更多来源见 `references/sources.md` 与 `config/source-registry.json`。
