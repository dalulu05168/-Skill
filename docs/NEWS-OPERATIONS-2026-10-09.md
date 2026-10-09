# B 方案：罗马尼亚金融资讯实际执行与仓库维护

## 最新现状
- 沿用 Romania Stock Intelligence V2.1 对来源、单位、时间、交易日、数值的结构审查与 SQLite 事件雷达。
- 已添加官方 BVB 的两种 RSS 读取脚本：显式下载、XML 解析、源内 GUID/内容哈希去重、修订识别、持久化候审队列。
- 重要性关键词只意味着人工优先审阅，不能证明真实影响、价格涨跌方向、来源事实或准确性。
- 当前没有在线采集服务、定时任务、已获授权实时行情接口、WhatsApp 发送器，也没有网页原文自动核实服务。不得把源码存在等同于这些能力已上线。

## 正式来源优先级
1. BVB 新闻 RSS：https://www.bvb.ro/Rss/StiriBVB.ashx
2. BVB 财务公告 RSS：https://www.bvb.ro/Rss2/LastFinancialData.ashx?lang=ro
3. BVB 发行人公告与 IRIS 原文、BNR/ECB/Eurostat 官方数据用于核实事实。参考完整 config/source-registry.json。

2026-10-09 GitHub Actions 已验证BVB新闻RSS可拉取未核验的候审数据；财务RSS仍缺少有效文章链接，必须隔离。网络采集不等于原文事实核验，站点使用许可亦须另行确认。程序拒绝向非许可源追踪重定向。离线 XML 不可证明发布方身份。

## 本地运行（Python 3.11+）
进入 .agents/skills/romania-stock-intelligence 目录：

    python scripts/rss_intake.py --source-id BVB_NEWS_RSS --fetch --state /private-data/news-state.json --out /private-data/news-review.json
    python scripts/rss_intake.py --source-id BVB_FINANCIAL_RSS --fetch --state /private-data/issuer-state.json --out /private-data/issuer-review.json

不联网时用 --input /path/snapshot.xml 替换 --fetch，输出 source_attestation 会明确标记为未认证的本地快照。持久状态必须放在仓库外、可备份的目录；各来源使用独立状态文件。首次出现标 new，完全一致标 unchanged，同一 GUID 内容变更标 revised。跨来源语义去重还未实现。

## 重大新闻和固定时段双轨
- 采集：事件取得原始来源 URL、article URL、标题、时间以及文本内容摘要，写入审核队列；无可用输入、源故障和解析失败必须显式失败。
- 去重：源内重复合并，修订重回审核；未来接入 Datasketch 与正文抽取工具时，将不同媒体对同一事件的转载聚合。
- 审核：打开一次来源原文核实其真实发布内容，再核时间、数值、单位、比较口径、原始股票代码和来源主体，证据不足为待核实。V2.1 audit 通过仅代表结构检查，不代表原文事实正确。
- 分流：重大新闻候选进即时审核提醒队列，其余进入当天对应固定节点资料包。按导演 Skill v2.3.0 的 Europe/Bucharest 16 节点课程表决定栏目，夏冬令时自动转换；旧 08/13/18 独立简报模板不可覆盖现行时间。
- 发布：审稿人确认包含出处、观察时刻、核心事实、罗马尼亚市场潜在传导及不确定性，批准后才可发布。未获授权不得直接发送 WhatsApp、Telegram、交易指令或用户故事。

这一版提供的是可测试的候审队列底座，尚未部署定时调度和人工审稿后台。

## 角色与仓库区分
- 本仓库导演模块保留 65 人 v4.1 全量资料和每人媒体许可。
- 本仓库人物唯一来源为导演 65 人 v4.1 档案，编号仅在本项目内有效；外部项目独立维护，严禁自动跨库对号、导入记忆、覆盖角色或同步课程。
- 现行导演 v2.3.0 规范教授仅在 19:30 正式晚课出场；教学对白标明虚构演绎，绝不冒充现实投资者见证。
- 只有用户明确采用的最终稿才能记为正式人物历史；草稿、测试样本、新闻模板不可入库。

## 自动化质量检查及安装包
从仓库根目录执行：

    python -m unittest discover -s .agents/skills/romania-stock-intelligence/tests -v
    python skills/romania-market-director/scripts/validate_persona_roster.py
    python tools/assemble_bundle.py --out-dir build/skill-bundles

GitHub Actions 的 Romanian Skill Quality Gate 会运行相同测试并生成可下载的 ZIP 工件，不发布群消息，不运行实盘。仓库现有 dist 文件仍可能为旧版，必须使用此次工作流验证生成的包，或在本机自行构建。

## 第二阶段建议：专项验收后再接入
- Trafilatura 提取完整原文，Datasketch 去重近似新闻，增加网页证据哈希与快照。
- Promptfoo 人物身份、表情、课程、数字准确度、幻觉和重复性基准测试。
- Langfuse 可观测追踪，生产持久数据库、人工审核队列及定时提醒器。
- 评价标准以测试案例实测统计为准，不凭空承诺准确率提升百分比。

## SKILL 融合第二阶段：候审可靠性修复（2026-10-09）

这次在原有四项专属 SKILL 与 65 人资料上**增量修复** BVB RSS，不改变角色、课表和其他仓库。

- 源内去重摘要现在包含标准化文章URL（保留文章路径和查询参数，忽略 #fragment）；即使标题/说明没变，真正更换文章链接也重新候审。
- 持久状态 JSON v2 将 `entries`（采集观察历史）与 `pending`（人工未审核的版本）分离。`--out` 现在输出**所有积压待审版本**，不能用“抓过一次”替代“人工审核过”。
- 同一GUID出现多次修订时，按 `item_id + digest` 保存各版本，新的更新不得覆盖尚未处理的旧版本。无有效RSS条目继续显式报错。
- 从旧 v1 迁移时：尚在RSS中、但只有旧采集摘要的文章标为 `legacy_unreviewed` 重新候审；旧摘要没有“已审核”的语义。状态文件和待审输出均采用同目录临时文件替换，减少写入中断造成的JSON损坏。
- `--state` 必须位于仓库外、可备份的持久目录；各个RSS来源使用**不同的状态文件**。不使用 `--state` 的一次性采集无法跨运行记住未审条目。

审核员核实原文后，可以创建一个**一次性**本地JSON文件，指定待移出的每个候审版本的准确标识：

```json
{"acknowledged":[{"item_id":"从候审JSON复制原值","digest":"从同一条候审版本复制原值"}]}
```

显式执行：

```bash
python scripts/rss_intake.py --source-id BVB_NEWS_RSS --fetch --state /private-data/news-state.json --out /private-data/news-review.json --ack-file /private-data/reviewed-once.json
```

未知的标识或不匹配摘要将拒绝，不能静默忽略审核错误。**审核确认只代表从待办移出，不代表事实核验通过，也不构成任何发布授权**；核验原始证据、审稿结论和发布审批另行留档。确认文件成功使用后，下一次普通采集不要重复带 `--ack-file`。

回归测试覆盖：重复采集仍待审、URL变更与片段、同GUID多次修订积压、源条目轮替、v1迁移、非法确认、离线CLI持久化。此修复不提供定时抓取、跨源语义去重或WhatsApp自动发送。
