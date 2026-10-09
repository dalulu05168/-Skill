# 罗马尼亚财经导演资料包

统一入口：[导演SKILL.md](skills/romania-market-director/SKILL.md)。完整版本和模块位置只看[bundle-manifest.json](bundle-manifest.json)，模块编号不是功能数量。

## 当前内容

- 导演流程：2.3.0；原表发布/备料各提前30分钟，中文自然信息，改为上午40–45条、下午约40条、晚上约45条的弹性合计目标，特殊情况调整，助理完整主题长话，成员自然短句互动，不固定轮流发言。
- 人物资料：65人v4.1，逐人语言、表情与媒体权限；默认中文审阅稿，人物保留原语言DNA。
- 资讯审核：V2.1，原始证据、口径、时间、比较基准和计算检查；结构通过不认证行情真实。
- 八项内容完整保留，前期优先签到及每日优质股研究信息/股票走势，自然穿插，不全部每天出现。
- 助理/教授观点结合当天已核验的大盘与资讯。理念课每周二/四，教授正文13–15段默认14段；技术课由用户提供。
- 原始聊天、表情明细、课程与记忆保留，草稿不自动成为已采用历史。

## 下载与更换GPT

推荐完整包：[romania-finance-bundle.zip](dist/romania-finance-bundle.zip)，包含导演资料与独立资讯审核模块，目录与仓库一致。较小的[导演单模块包](dist/romania-market-director-skill.zip)仅包含导演目录，不含资讯代码。**注意：仓库源码已更新至2.3.0，但dist中的两个ZIP尚未重新打包，现为旧版本；跨GPT导入前须重新构建。** 两个包的内容范围仍不同。

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
[强制身份核对、GIF/新闻图片触发、三时段八项、最终角色记忆](skills/romania-market-director/references/identity-media-memory-workflow.md)；独立验证器`skills/romania-market-director/scripts/validate_persona_roster.py`。新闻数字核验在人物选角前；编号姓名性别新老四重比对。助理八项上午/下午/晚上各一条；GIF合规随机且场景匹配；有真实图片任务立即执行而非只写占位。用户明确确认修改定稿时，具备权限的会话须归档原文及`memory/state.json`并核验GitHub提交。原独立教授Skill路径在历史v1.2文件中有引用，但当前仓库未保存原件；晚间19:30课程仍按现有规则及可获得讲稿执行。旧dist ZIP尚未重建。

## 资讯与维护增强（2026-10-09）

- [B 方案新闻接入、审核和发布执行说明](docs/NEWS-OPERATIONS-2026-10-09.md)。现已增加官方 BVB RSS 人工审核候选队列与去重测试，但**没有**开启实时行情、定时推送或自动审稿发布。
- 运行 `python -m unittest discover -s .agents/skills/romania-stock-intelligence/tests -v` 和 `python skills/romania-market-director/scripts/validate_persona_roster.py` 回归测试。
- 运行 `python tools/assemble_bundle.py --out-dir build/skill-bundles` 从当前源码生成两个 ZIP，或者使用 GitHub Actions 的 `Romanian Skill Quality Gate` 工件。旧 `dist/` ZIP 未自动替换，不可声称已同步最新版。
- 此处只保留本仓库 65 位 v4.1 成员档案与导演规则；不读取、写入、覆盖或同步任何其他项目的人物、课程、记忆及交易信息。人物编号只在本仓库内有效。

## BVB准确性增强技能 v1.0

新增[准确性增强包](skills/accuracy-enhancement/README.md)：4项专属SKILL、6份MIT开源技术参考，全部纳入完整版可重建ZIP和CI检查。保留原导演/新闻核验技能及65名v4.1人物文件、现行16节点与审批约束。

此项仅集成文档及质量门禁指南；未安装Python第三方依赖、未实现跨来源语义引擎、未恢复500行情接口、未自动群发。使用`python tools/test_accuracy_pack.py`做静态检查。
