# P004 Fiction Director · 新独立工作区

本目录是新大型 Skill 的唯一开发入口。目标是从第一场开始打造65名具有不同语言性格、能够产生被记录的后续记忆、由总导演调度的连续虚构财经群聊小说。

## 与旧资料物理隔离

- 旧目录：`skills/romania-market-director/`（不修改、不重命名、不删除）。
- 新目录：`skills/p004-fiction-director/`（**单独的 Skill 名称、配置、未来人物档案和记忆状态**）。
- 不使用旧的 `characters/index.json`、`characters/profiles/*`、`memory/state.json`，不从另一套70/72人或旧65人资料自动填充。
- 本次先创建空白新记忆及角色模式，人物名称、分组及全档案仍待用户确认，避免首次建档就遗留旧设定。
- 现有模块二的独立交易账本**不复制**到本目录；未来只读查询时需要角色 ID 对应映射由用户确认，而且必须是已完成的 `buy/sell`，不可依据推荐推断成交。
- 模块四继续独立，不迁入4K页面，也不增加生成图片/翻译。
- 此版本先留在独立开发分支和草案 PR，未经合并/部署验收，不称上线。

## 推荐研发顺序
1. 确定虚构教授与助理的独立人格和口吻；经样例对话测评。
2. 逐个定义新65名人物：主次发言倾向、语言DNA、兴趣触发和沉默习惯；进行身份及差异性测试。
3. 实现本目录独立正式记忆（仅从被采用的场次更新）。
4. 完成财经研究只读事实输入与模拟交易已成交记忆输入。
5. 总导演/编剧形成连续时间段内容；临时插播后重新编排未交付内容。
6. 自动结构化回归测试、人工文学性审稿和实操验收。

## 免费路线
先依靠零额外付费的文本规范、Python标准库/JSON Schema、本地文件和现有AI会话做手动触发。外部开源框架仅作为**候选**；其代码许可不等于模型推理免费。不安装未评估的大型框架，不导入外部人的真实数据、演示交易或虚构资产。

## 第一阶段：不用 Mem0 的独立 SQLite 记忆账本（2026-10-11）

- 可执行代码：`scripts/scene_memory.py`（Python 3.11 标准库 sqlite3，不需安装包、不依赖模型/API）。
- 执行测试：`python -m unittest discover -s skills/p004-fiction-director/tests -p 'test_*.py' -v`。
- 只认新故事 `story_id=p004-fiction-director-independent`，只从 `characters/approved-roster.json` 中读取经确认的新角色编号；此文件目前**空白**，不使用旧65人档案。
- 只接受 `simulation_only=true` 且 `approved_by_user=true` 的正式场次，并要求调用方明确传 `operator_confirmed=True`；按 scene_id、message_id、日期、speaker_id 存入 SQLite。
- 相同 scene_id 重复导入相同内容会去重；内容不同直接拒绝，不能悄悄覆盖已采用的历史。无记录时按空历史处理；可按人物+关键词检索并核验引用是否确实存在。
- 该数据库**不导入模块二交易记录**；待新角色编号经确认后再开发模块二已成交交易的只读适配器。
- `memory/state.json` 是历史的**空白启动标记**，不是 SQLite 已采用记录的同步副本。后续一旦启用 SQLite，正式剧情记录以该数据库为准，不把两套状态自动双向同步。数据库文件默认在运行机器本地，已用 .gitignore 防止误提交；正式部署仍需持久卷/备份，容器临时盘不能保证持久。
- 当前尚未与 `/skill` 页面、自动AI导演或正式发布操作联通。记忆引擎通过模块函数调用，不能据此声称已自动学习整天剧本。

## 第二阶段成果：65人候选档案（草案）

- 完整数据：`characters/drafts/roster-v1.json`；
- 手机上便于逐人浏览：`characters/drafts/roster-v1-review.md`；
- 创作机制：`references/member-director.md`；
- 初始一天的角色互动样例：`examples/first-day-ensemble-audition.md`；
- 结构化角色检测：`scripts/validate_draft_roster.py` 与 `tests/test_draft_roster.py`。

所有65人现在还是 `approved_by_user=false`，与真正确认的 `characters/approved-roster.json` 分开。不能把候选人物的样例台词当成历史，也不能把候选姓名编号自动映射到模块二的交易账户。

已进行逐字段、人数、独特口癖与专业领域等JS数据结构验证；新增Python自动化测试尚需在可执行环境运行，不能把GitHub中出现测试文件当成测试已通过。

## 第三阶段成果：65人 v2 口吻修订与自动验收

- **优先审阅**：`characters/drafts/REVIEW-65-v2.md`（五批次中文索引，含65人罗马尼亚语试听句）。
- **新版候选**：`characters/drafts/roster-v2.json`（独立主次倾向、职业、兴趣、口癖、主动出场/被反驳反应、零历史）。原`roster-v1.json`留作差异对比，未删除。
- **确定性检查记录**：`characters/drafts/QA-v2.json`，结构检查并非文学审稿；不存在任何已批准新角色。
- **三时段虚构排演**：`examples/65-person-multiscene-audition-v2.json`，共26条，包含成员互答、下午接上午话题、周三晚课；没有实际BVB行情数值或交易事实，未采用为正式剧情。
- **Python检查**：`scripts/validate_draft_roster.py`、`tests/test_draft_roster.py`、`tests/test_multiscene_audition.py` 和已有记忆测试。
- **GitHub Actions独立QA**：`.github/workflows/p004-independent-director-qa.yml`，只监控新目录变更，运行Python 3.11标准库测试；不会执行/导入旧人物Skill源码。该workflow是唯一新增在隔离目录外的文件，属于CI配置，旧程序及人设均未改动。

任何机器通过均不表示罗马尼亚语地道程度或小说真实感已经合格。正式名册`characters/approved-roster.json`继续为空。还需用户逐批定人设后，才可正式导演多日剧情和映射模块二模拟成交。

## 第四阶段：初版导演自动选角（沙盒功能）
`scripts/director_cast.py` 是**已实现的、无需付费模型API**的确定性选角程序。它读取本目录待确认`roster-v2.json`，接受假设话题、场次、日期、成员上场情况，依据兴趣、职业和时段给候选角色打分，并尽量避免只有一种主行为类型出场。每张候选卡保留角色ID、选角原因、语言习惯和“可以沉默”状态；仅返回选角计划，**不会自动编写真实对白、查询新闻、读模块二交易、写剧情记忆或发布群消息**。

示例输入：`examples/cast-request-energy.json`。试运行（需Python 3.11）：
```bash
python skills/p004-fiction-director/scripts/director_cast.py --request skills/p004-fiction-director/examples/cast-request-energy.json
```
编辑`topic_keywords`、`story_date`、`daypart`、`recent_member_ids`即可尝试其他假设场景。人物全部未正式批准，结果标记`draft_only=true,publishable=false`，不能拿来冒充真实群成员讨论。测试位于`tests/test_director_cast.py`，CI只覆盖可以机械确定的逻辑，不意味着编剧输出的文学性已被验收。
