# 罗马尼亚财经资讯与课程编剧

Skill入口：[SKILL.md](skills/romania-market-director/SKILL.md)。完整人物档案：[characters/profiles/](skills/romania-market-director/characters/profiles/)。

市场规则：罗马尼亚股市及影响其波动的消息优先，其次美股与其他国家；整理指标数值、来源、时间与影响逻辑，不处理买卖指令。剧本为明确标注的虚构教学演绎。

## 更换GPT后如何使用

支持GitHub访问或连接器的GPT：打开本仓库，读取Skill入口与人物索引，选角后读取对应完整JSON档案。不能访问仓库的GPT：下载 `dist/romania-market-director-skill.zip` 并上传。GPT不能解压时，在本地解压，上传SKILL.md、references文件和人物索引，再按选角补充完整人物档案。

可复制的启动语：

> 请读取本资料包的SKILL.md和characters/index.md，按罗马尼亚优先的规则工作。根据本场主题选角，再读取入选者的完整档案。编排明确标注为虚构的剧本；新闻和指标需要核验，缺数据不编造，不处理买卖指令。本场需求是：……

## 课程与能力

理念课程按Europe/Bucharest当地每周二、周四备课，首次授课日期尚未设定。每周一、三、五可准备有证据的个股研究，不提供买卖指令。技术课程由用户准备。

Skill本身不自动运行、不自动群发、不永久保存对话。实时检索取决于GPT工具与网络权限。新GPT实际端到端生成尚未测试，不能保证所有平台自动加载本仓库。

[上午离线试稿](skills/romania-market-director/examples/上午离线试稿.md)仅使用明确标注的假设数值，用于检查人设和结构，不是今日行情。


## Romania Stock Intelligence — Codex 金融分析技能

已加入 Codex 可自动发现的项目级 Skill：[.agents/skills/romania-stock-intelligence/SKILL.md](.agents/skills/romania-stock-intelligence/SKILL.md)。与原有 [罗马尼亚财经资讯与课程编剧](skills/romania-market-director/SKILL.md) 并列、相互独立。

使用：在 Codex 打开本仓库，重新开启会话，输入 `$romania-stock-intelligence` 加上任务；或者参考 [Codex 安装说明](.agents/skills/romania-stock-intelligence/CODEX-README.md) 安装到用户级 `~/.agents/skills`，以供其他仓库调用。Skill 本身不会生成实时行情或创建自动任务。


## 金融情报引擎 V2.1（Codex）

[SKILL.md](.agents/skills/romania-stock-intelligence/SKILL.md) 已升级至 V2.1，保留既有 `romania-market-director` 人设与课程。新增 [V2-README.md](.agents/skills/romania-stock-intelligence/V2-README.md) 与 `scripts/rsi_v2.py`，实现本地数据核验、BET成分贡献估算、事件雷达、SQLite 历史记录、证据驱动教授课程。Python 3.11+ 标准库即可执行；通过 `python -m unittest discover -s tests -v` 验收。合成测试样例非真实行情，实时市场数据、定时推送与自动群发不在本次部署范围。

## 当前导演流程：2.0.0

上午建立背景与理解，下午根据新证据推进；现行流程只读取 [daytime-rhythm.md](skills/romania-market-director/references/daytime-rhythm.md)，对话节奏读取 [director-workflow.md](skills/romania-market-director/references/director-workflow.md)。旧示例与草稿不作为当前格式规范。保留上午50条、下午45条，不能拆句凑数。

## 65人角色库 v4.1（2026-10-09）

`skills/romania-market-director/characters/profiles/` 中65份JSON已升级为逐人审校的 v4.1，含短句、问候、Emoji、GIF/PNG许可、沉默及个人语言优先级。读取规则：[persona-media-v4.1.md](skills/romania-market-director/references/persona-media-v4.1.md)；审校报告：[characters/v4.1/](skills/romania-market-director/characters/v4.1/)。

**媒体存放说明**：本仓库已保存65份角色JSON、审核与媒体索引；12个GIF和8个PNG的原始二进制当前位于[Google云盘v4.1目录](https://drive.google.com/drive/folders/1VmWPcnbmLc5UNomI-S3QPBRPa93TtxTs)，尚未作为二进制写入本GitHub仓库。`dist/romania-market-director-skill.zip` 尚未由此提交重新构建，请优先读取仓库中的实时文件，不要把历史ZIP当作v4.1。
