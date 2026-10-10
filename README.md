# 罗马尼亚财经导演资料包


## 已确认的全站UI与65人唯一人物来源（2026-10-10）

- **设计依据：**用户确认的16:9纯白底、浅灰细框金融后台设计；对应可编辑 [Canva设计稿](https://canva.link/5m4bz4st652dwrf)。该设计稿供后续编辑和视觉对照，代码以已实现的本地页面为准。
- **四个入口，职责分离（不是三个交易平台）：**`/` 新闻与审核、`/trading` 65人模拟交易与持仓、`/skill` 课程/群聊脚本/正式会话与记忆、`/trade-platform` 第三方入口。全部统一纯白背景、灰色细边框、深色文字、轻量悬停起伏与移动端响应式布局；旧 `/writing` 兼容访问 Skill。
- **65人唯一授权来源：**`skills/romania-market-director/characters/index.json` 与全部65份正式 `profiles/*_AI_Profile.json`；每次读取由独立校验器交叉确认，拒绝不存在的编号和错配的姓名/性别/新老分类。旧70/72人人物资料和历史**不导入统一系统**，旧单独仓库未被破坏或删除。
- **信息必须真实：**首页人物表格的编号、名称、职业和城市来自正式人物索引；成员为**明确标识的虚构教育角色**，并非真实投资者。无WhatsApp在线状态接口时一律“未知”；无行情/活动记录时不展示虚构曲线、股票价格、收益或更新时间。四张卡片只显示本机已保存的新闻审核包、真实采用会话和65人正式档案，未执行时显示缺失状态。
- **不破坏原功能：**新闻候审、BVB RSS 核验、16节点、Ollama可选内稿以及65人正式档案仍保留；ChatGPT提示词、正式会话、角色记忆和课程文档集中在 `/skill`，不再占用交易页面。第三方网站仅安全跳转，不声称已接通外站登录、持仓、资金或交易。
- **验收方式：**`python -m unittest discover -s tools -p 'test_canva_dashboard_ui.py' -v`，与原CI中的API/人物/新闻自动测试一同执行。GitHub绿灯不代替用户电脑的真实浏览器截图比对，也不等于公网部署。

## 📰 新闻推送 × 💹 65人模拟交易 × 🧠 财经 Skill × 🖼️ 图片编辑器

**同一工作台、四个清晰入口：**双击 `START-FINANCE-SKILL.cmd` 后在浏览器打开 `http://127.0.0.1:8765/`。页面侧栏可切换“新闻推送”“交易中心”“财经 Skill”“外部图片编辑器”。人物资料从同一个65人v4.1正式来源读取，交易记录和已采用的会话记忆仍独立保存。

- **新闻推送：**沿用RSS候审、核验、16节点、65人身份约束与发布闸门。
- **交易中心 `/trading`：**读取本仓库65份正式v4.1人物AI档案，提供人物资料、模拟开户及资金条件、股票计划、推荐与邀请、模拟买入、持仓、卖出和交易事实记录；页面不呈现课程、群聊脚本、会话记忆。
- **财经 Skill `/skill`：**集中课程与文档、助理/教授原话和群聊脚本、正式采用会话、人物记忆规则及人物选角。旧 `/writing` 兼容访问 Skill；不覆盖65人固定档案。
- **外部图片编辑器：**新增本机 `/trade-platform` 模块，供用户从工作台点击访问 [trade.sasakic.cc](https://trade.sasakic.cc/)；这是**显式外部跳转**，不是代码/账户/资产/交易接口的合并。目标站点目前无法由本环境确认可访问性、登录要求或允许被嵌入，因此不使用iframe或虚构其功能。
- **数据隔离：**人物身份仅以 `skills/romania-market-director/characters/profiles/` 为准，不跨库引入或按编号误认72人角色；写作状态单独保存在本机 `~/.romania-finance-skill-hub/chennan-writing-65.json`，不会覆盖新闻候审状态，也不自动导入旧项目已有历史。
- **能力边界：**当前为**本地整合版**；Skill 的结构化多人草稿仍需复制提示词到现有ChatGPT生成、再粘贴JSON校验；交易中心的买卖记录仅为人工确认的65人模拟账本，新闻推送模块另提供可选本机Ollama单次教育草稿生成（需预先安装模型）。没有自动群发、实盘交易或云端同步。原独立72人旧站未被删除，原历史没有转换。

完整说明：[统一财经SKILL工作台](docs/UNIFIED-FINANCE-SKILL-HUB.md) · [新闻资讯审核规则](docs/NEWS-OPERATIONS-2026-10-09.md) · [旧独立72人站点（保留，不混用）](https://growth-story-workspace.vercel.app/)


统一入口：[导演SKILL.md](skills/romania-market-director/SKILL.md)。完整版本和模块位置只看[bundle-manifest.json](bundle-manifest.json)，模块编号不是功能数量。

## 首选：使用已有 ChatGPT，不用安装本地模型

**你的 GPT 可以直接承担多人教育稿的内容生成。** 在电脑双击 `START-FINANCE-SKILL.cmd`，选择“财经 Skill”，勾选人物 → 输入助理或教授已核实的内容 → 生成完整提示词 → 复制到已有的ChatGPT／自定义GPT → 将其JSON回复粘回 Skill 校验 → 人工确认后归档。人物档案来自**本仓库65人v4.1**，不导入外部72人项目；使用这个方式**无需Ollama，也无需另买API额度**。

这属于**人工在ChatGPT中交互**，不是本地网页自动调用你的ChatGPT订阅模型，亦不保证任何特定自定义GPT拥有GitHub访问权限。需要完全无人值守的站外调用，应另行评估是否支持“使用ChatGPT登录”的正式授权集成或独立API方案，不能伪造登录令牌绕过限制。详细步骤见[使用我的ChatGPT操作说明](docs/CHATGPT-FIRST-WORKFLOW.md)。

## 统一财经 SKILL 工作台（新增）

**不再需要每天下载ZIP**：在已取得的仓库源码目录内，Windows可双击 `START-FINANCE-SKILL.cmd` 启动本地浏览器工作台；其他系统执行 `python tools/finance_skill_api.py --open-browser`。入口自动路由 BVB 新闻候审、行情数据结构检查、16节点课程、65人身份与最终人工审稿门禁，完整能力与限制见 [统一工作台说明](docs/UNIFIED-FINANCE-SKILL-HUB.md)。这只是本机运行，不表示网址已部署或真实AI模型已生成台词。

**新增本机 AI 教育草稿**：已把可选 Ollama 生成按钮接入工作台，可按当前16节点选择助理、教授或65名虚构成员。需要用户本机先安装 Ollama 与受支持模型，启动后才能实际生成；不使用模型时仍可运行资讯候审和规则审核。使用方式见[统一SKILL工作台](docs/UNIFIED-FINANCE-SKILL-HUB.md)。模型内容始终为未核实内部稿，不会自动群发。

## 当前内容

- 导演流程：2.3.0；原表发布/备料各提前30分钟，中文自然信息，改为上午约35条、下午约35条、晚上约30条（各允许上下浮动2–3条）的弹性合计目标，特殊情况调整，助理完整主题长话，成员自然短句互动，不固定轮流发言。
- 人物资料：65人v4.1，逐人语言、表情与媒体权限；默认中文审阅稿，人物保留原语言DNA。
- 资讯审核：V2.1，原始证据、口径、时间、比较基准和计算检查；结构通过不认证行情真实。
- 八项内容完整保留，前期优先签到及每日优质股研究信息/股票走势，自然穿插，不全部每天出现。
- 助理/教授观点结合当天已核验的大盘与资讯。理念课每周二/四，教授正文13–15段默认14段；技术课由用户提供。
- 原始聊天、表情明细、课程与记忆保留，草稿不自动成为已采用历史。

## 下载与更换GPT

资料包统一从[GitHub Actions 的 Romanian Skill Quality Gate](https://github.com/dalulu05168/-Skill/actions/workflows/skill-quality.yml)下载最近一次**成功的 main 分支构建**所附的 `romania-skill-bundles`，解压后有完整包 `romania-finance-bundle.zip` 和导演单模块包 `romania-market-director-skill.zip`。两者范围不同；不要再使用过去提交在 `dist/` 的过期二进制。构建产物保留14天，过期时可以手动运行该工作流，或在本地运行 `python tools/assemble_bundle.py --out-dir build/skill-bundles`。

支持文件解压和读取的GPT：上传完整包并说明“先读README.md和bundle-manifest.json，再读导演SKILL.md，按当天需求读取资讯、完整人物、素材与记忆”。不支持解压的平台需先本地解压，分批上传规则与所需资料。运行Python审核代码需要代码工具，知识文件上传本身不会执行代码。

有GitHub访问能力的GPT可读取本仓库，Codex项目级资讯Skill在`.agents/skills/romania-stock-intelligence/`。仓库链接、云盘或其他窗口不会自动同步到所有GPT，不能假定已连接。

## 媒体现状

原有5个GIF及MP4已本地保存。新v4.1的12个GIF与8个PNG目前只有索引及[云盘链接](https://drive.google.com/drive/folders/1VmWPcnbmLc5UNomI-S3QPBRPa93TtxTs)，不包含在下载包中。角色许可优先，新旧素材ID不得互换，未读取/未发送的素材不声称已使用。

## 能力与边界

所有多角色对白均为明确标注的虚构教学演绎，不冒充真实投资者或客户见证，不处理买卖指令。Skill不能自动取得实时行情、安装连接器、读取其他GPT推送、创建任务或向WhatsApp发送消息。

资讯代码验证：在`.agents/skills/romania-stock-intelligence/`运行`python -m unittest discover -s tests -v`。合成测试数据不能作为实际行情。新GPT端到端生成能力未由打包检查证明。

## 当前最高优先级
[2026-10-09统一执行标准](skills/romania-market-director/references/operating-standard-2026-10-09.md) · [国际新闻配图标准](skills/romania-market-director/references/news-visual-standard.md) · [跨GitHub工具入口](AGENTS.md)。更新GitHub不等于所有ChatGPT窗口自动安装。本库保留导演、资讯核验两个有效Skill，没有确认可安全删除的废弃技能。

## 当前v2.3.0一体化执行标准
[强制身份核对、GIF/新闻图片触发、三时段八项、最终角色记忆](skills/romania-market-director/references/identity-media-memory-workflow.md)；独立验证器`skills/romania-market-director/scripts/validate_persona_roster.py`。新闻数字核验在人物选角前；编号姓名性别新老四重比对。助理八项上午/下午/晚上各一条；GIF合规随机且场景匹配；有真实图片任务立即执行而非只写占位。用户明确确认修改定稿时，具备权限的会话须归档原文及`memory/state.json`并核验GitHub提交。原独立教授Skill路径在历史v1.2文件中有引用，但当前仓库未保存原件；晚间19:30课程仍按现有规则及可获得讲稿执行。旧dist ZIP不再作为当前下载源，使用质量检查构建产物。

## 资讯与维护增强（2026-10-09）

- [B 方案新闻接入、审核和发布执行说明](docs/NEWS-OPERATIONS-2026-10-09.md)。现已增加官方 BVB RSS 人工审核候选队列与去重测试，但**没有**开启实时行情、定时推送或自动审稿发布。
- 运行 `python -m unittest discover -s .agents/skills/romania-stock-intelligence/tests -v` 和 `python skills/romania-market-director/scripts/validate_persona_roster.py` 回归测试。
- 运行 `python tools/assemble_bundle.py --out-dir build/skill-bundles` 从当前源码生成两个 ZIP，或者使用 GitHub Actions 的 `Romanian Skill Quality Gate` 工件。`dist/` 的旧 ZIP 已停止提供；请下载当次通过验证的构建产物，或自行从当前源码重建。
- 此处只保留本仓库 65 位 v4.1 成员档案与导演规则；不读取、写入、覆盖或同步任何其他项目的人物、课程、记忆及交易信息。人物编号只在本仓库内有效。

## BVB准确性增强技能 v1.0

新增[准确性增强包](skills/accuracy-enhancement/README.md)：4项专属SKILL、6份MIT开源技术参考，全部纳入完整版可重建ZIP和CI检查。保留原导演/新闻核验技能及65名v4.1人物文件、现行16节点与审批约束。

此项仅集成文档及质量门禁指南；未安装Python第三方依赖、未实现跨来源语义引擎、未恢复500行情接口、未自动群发。使用`python tools/test_accuracy_pack.py`做静态检查。

## 2026-10-10 高情商编剧 / 有源长期记忆增强（待合并测试）
- 新规则：[高情商编剧与可追溯人物记忆](skills/romania-market-director/references/high-empathy-storycraft-v2.md)。65位角色通过各自完整档案保留性格、语言、情绪、相互关系和自然沉默，避免机械赞美、空话和没来由的历史。
- 新校验：`tools/storycraft_contract.py` 结构阻断无效历史引用、交易施压与贬低；语气、主题关联和元台词只提示编辑，不能替代真人审稿。
- 已采用会话可以通过 `session_id + message_id` 回溯；未采用草稿不生效；本机历史不自动同步到所有GPT或GitHub，正式仓库初始记忆为空不表示已拥有客户聊天。
- 工作台对白阅读预览将身份说明与**人物说出的正文**分开显示；审稿JSON、单独导出和外部流转仍保留必要身份说明。没有 WhatsApp 群发、金融事实自动认证或真实交易能力。
- 当前全日弹性数量以最新 `operating-standard-2026-10-09.md` 的 **上午35/下午35/晚上30（±2–3）** 为准，历史说明中的40–45/40/45作废。

## P004 新增三层角色语言标准（2026-10-10）
原65人完整档案没有重建。写稿时自动生成逐人独立 `selected_personal_voice_briefs`；成员使用简短日常口语，助理专业易懂，教授高度专业。见 [角色说话层级及示例](skills/romania-market-director/references/member-assistant-professor-voice.md)。代码 `tools/role_voice.py` 会拦截明确的成员越权推荐和交易施压，对研报腔、不同人复制句子给出人工修订警告，不能取代真人语感验收或行情事实核验。
