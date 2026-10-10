# 统一GitHub工作入口（罗马尼亚财经群）

**本机AI扩展（可选）**：仅允许 `tools/finance_skill_generate.py` 通过127.0.0.1的Ollama接口生成内部教学草稿，前台入口为 `tools/finance_skill_api.py` 的“检查本机模型／生成内部教育草稿”。不得将模型输出当成来源核验或真实客户见证，教授仅RO-10工作日晚课出场；65名角色从本仓库v4.1完整档案逐位验证。模型不可用则诚实报错，不伪装生成成功，也绝不自动对外发消息。

**统一可执行任务入口（新增）**：若环境支持执行Python代码，优先使用仓库根目录 `python tools/finance_skill_hub.py`，本机界面为 `python tools/finance_skill_api.py` → `http://127.0.0.1:8765/`。按 `docs/UNIFIED-FINANCE-SKILL-HUB.md` 顺序协调BVB候审、来源元数据审核、16节点课程、65人身份、审稿门禁。RSS须显式 `--fetch-rss` 和仓库外状态文件；此入口**不等于已核实市场、已生成真实AI对白或已发送群消息**。无法运行代码的GPT只能读取规则并明确限制，不得虚构工具调用。
当请求涉及罗马尼亚BVB群聊剧本、人物调度、财经资讯验证或新闻配图时：
1. 阅读`skills/romania-market-director/SKILL.md`和`skills/romania-market-director/references/operating-standard-2026-10-09.md`。
2. 新闻使用`.agents/skills/romania-stock-intelligence/SKILL.md`核验，选择65人中的角色需读取本人完整`characters/profiles/`档案。行业/市场影响范围必须分析，新闻输入不等于已核验。
3. 所有时间使用Europe/Bucharest，按最新16节点发布和备料均比原计划提前30分钟；**各阶段只能执行对应课程表栏目，承接上段而非重复开群**；正文仅栏目标题有时间、人物讲话无时间。默认中文，新老男女备注，非机械交替，正常合理不同意见不是每句反驳；重要国际新闻16:9罗语配图，左上原始透明Logo。
4. **项目核心为短线交易与盘前/集合竞价/盘中机会研究**，不得笼统否定短线；可讲条件策略和风险，但没有用户具体买卖票不得自编真实交易。教授仅在晚间导师晚课正式出场。财经角色是虚构教学演练，不冒充真人客户或交易结果。未授权不创建定时任务、不发送群消息。
5. 这是仓库内统一入口，不等于自动安装到所有ChatGPT页面；只有具备权限且主动读取本仓库的会话才会执行。

6. **当前消息节拍 v2.2.1**：工作日上午40–45条、下午约40条、晚上约45条，每一大时段所有课表栏目累计；特殊行情/课程灵活调整。先删除不重要消息和重复段落，不能为凑数添加虚构行情、客户见证、无意义附和或强制反驳；仅生成单一栏目不得按完整时段凑40条。详见统一标准。

7. **导演v2.3.0硬顺序**：核查用户新闻指标原始来源和时间→确认16节点课程→从角色完整JSON及索引比对编号姓名性别新老类别（07 Ioana Petrescu新女；11 Florin Dobre新男，任何冲突不得出场）→挑选人物写稿→GIF根据本人许可、真正可用素材与语义随机/轮换→新闻视觉有明确配图指令则实际调用可用工具（真实分时曲线不得编）→上午、下午、晚上助理各一次八项内容→用户明确采纳最终稿后生成角色动态记忆并在有权限时写仓库或授权云盘。教授仅19:30出场，周一/三/五技术课、周二/四理念课，少数角色自然互动。旧独立教授Skill原件尚未保存到本仓库，不能谎称已使用。入口`skills/romania-market-director/references/identity-media-memory-workflow.md`。

8. **新增准确性增强技能（增量、不得覆盖上方最高标准）**：事实核验`skills/bvb-fact-check/SKILL.md`→新闻候审分级`skills/news-priority/SKILL.md`→模拟角色四重核验`skills/character-consistency/SKILL.md`→最终质量门禁`skills/script-qa/SKILL.md`。详见`skills/accuracy-enhancement/README.md`。第三方技术文件只读参考，不视为本系统已部署服务或运行权限。

## 2026-10-10 当前最高优先级：编剧连贯性与证据质量
先读 `skills/romania-market-director/references/high-empathy-storycraft-v2.md` 和 `skills/romania-market-director/references/mandatory-execution-contract.md`；人物跨场回忆必须链接到已经采用的场次/消息。新程序 `tools/storycraft_contract.py` 已用于本地写作保存前的检查；“历史似乎存在”“上游声称已验证”“模型说已经发送”均不可当证据。台词正文可自然，不让角色解释作者或系统设定；作品整体及单独流转内容必须诚实披露角色性质，不能伪装真人投资群、收益或客户背书。

**纠正本文件第6条的过期节奏：2026-10-10 以 `operating-standard-2026-10-09.md` 最近新增的 35/35/30 为准（上午约35、下午约35、晚上约30，各±2–3）；旧40–45/40/45完全废止。** 该数量只作弹性编排参考，不用于强制凑句，16节点及19:30教授出场规则不变。
