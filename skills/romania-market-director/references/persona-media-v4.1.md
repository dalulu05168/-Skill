# 65人v4.1短句、Emoji与媒体行为

- **正式来源**：`characters/profiles/` 中01–65号完整JSON；人设、语言、习惯、投资知识边界以本人档案为准。
- **审核资料**：`characters/v4.1/` 中的逐人审核表、修复记录、验收结果及媒体索引。
- **不更改**：导演版本只读取根部`VERSION`，角色资料独立版本为4.1；二者不是功能清单。
- **真人自然感**：日常优先1句或1–2句，根据角色原设定可更短；复杂讨论按本人最大句数，不强制用满。开群时部分先问好，中途进场可直接回复；自然沉默、追问或回应其他成员。
- **Emoji**：遵守本人 `language_dna.表情习惯`、v3表情管理与次数软上限；不要求人人附表情。
- **GIF/PNG**：遵守本人 `language_dna.媒体行为管理_v4` 中 `媒体许可策略`、`媒体动作可选`、素材ID、使用限制；禁用GIF的14人不能发GIF；其余51人也不强制发送。
- **语言优先级**：`language_dna.角色语言执行_v4_1`。05、30、37号以法语为主，纯罗语环境原则上不强制出场；其他人保留原语言设定。中文人物样例只用于理解，不直接作为罗语发言。
- **媒体素材**：`characters/v4.1/media_catalog_v4.json` 包含12个GIF/8个PNG的文件名与ID。**GitHub中当前只有索引，没有这20个原始二进制素材**；文件真实存于[云盘v4.1目录](https://drive.google.com/drive/folders/1VmWPcnbmLc5UNomI-S3QPBRPa93TtxTs)（[GIF目录](https://drive.google.com/drive/folders/1HaYTkvLbTyptHyIManOOwicf82SXYbhf)、[PNG目录](https://drive.google.com/drive/folders/10F0ANQXJy731cMgGH4iHhLJ1oPe3pWOe)）。未下载成功时只输出素材建议和链接，不得声称已生成/已发送图片。
- **用途边界**：资料中的角色均为明确标注的虚构教学演练角色，不得冒充真实客户、真实投资者或伪造真实交易收益及群体共识；不自动向WhatsApp发消息。
- **包版本提醒**：`dist/romania-market-director-skill.zip` 尚未按当前v2.2.0重新打包（旧ZIP不是最新执行标准）；人物JSON已在主分支保持65份，20个新媒体二进制仍未下载。

## 中文导演版补充
当用户明确指定中文时，先按本人原始语言DNA和性格转为自然不同的**中文审阅稿**，不能以“罗语默认”压过用户指令。署名必须用原档案`source_profile.学员资历`标新男/新女/老男/老女，不按序号推断。国际新闻配图见[news-visual-standard.md](news-visual-standard.md)。

## 强制身份四重校验与GIF匹配（v2.3.0）
挑选角色之前**必须读取角色完整JSON**及`characters/index.json`同编号项，核`character_id`=文件名前缀=index.id、`identity_extension.姓名`=index.name、`source_profile.性别`=index.sex，及`source_profile.学员资历`在老男/老女/新男/新女中且末字与性别一致；不通过不得出场。生成时写“编号｜姓名｜标签”，不得从年龄/编号推断。已知回归陷阱：07是Ioana Petrescu/女/新女，11是Florin Dobre/男/新男。若可运行Python，先执行`scripts/validate_persona_roster.py`。
在**允许GIF**的角色里，依据当前语义和人物性格/频率、媒体策略与真实可用素材进行变换/随机选择，不预先分配固定张数；禁用GIF者可以用其许可表情/文字，候选GIF不可忽略版权或缺文件问题。GIF编号旧/新隔离，图像出场后进入正式采用记忆便于避免重复。详见`references/identity-media-memory-workflow.md`。
