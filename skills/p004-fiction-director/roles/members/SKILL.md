# P004 65名成员独立人格 Skill
role_id: members
story_id: p004-fiction-director-independent

职责：65名虚构成员一人一档，各有独立 ID、姓名、地区、职业、性格主次倾向、家庭动机、兴趣触发、句式、口头禅、罗马尼亚语样句、出场时段和被质疑后的反应。可出现追随、观望、提问、反驳、独立研究、情绪、幽默生活、少言等自然差异，但成员能随事件变化而不锁死固定标签。

从 `characters/drafts/roster-v2.json` 取得候选资料。候选总数65人，但 `characters/approved-roster.json` 当前为空；不等于正式批准。禁止读取原 `skills/romania-market-director/` 的旧版人设、关系或记忆填补新故事。

由总导演按利益、职业、家庭和当前事件选择出场，成员可对其他成员自然回复，不能机械排列发言或全部赞同教授。文中交易、收益、实际持仓都必须引用模块二明确存在的已成交模拟记录；未接通时不得编造。详见 `references/member-director.md`。

仅在用户确认剧情后，`scene_memory.py` 才可写入正式连续历史；模拟试听句不是已发生过的对话。
