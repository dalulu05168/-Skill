---
name: character-consistency
description: 按65名v4.1人物完整档案核验教学模拟对白人物身份和一致性。
---
# character-consistency — 罗马尼亚金融内容准确性技能
## 数据边界
本仓库权威人物来源是 `../romania-market-director/characters/index.json` 与`../romania-market-director/characters/profiles/`中的**65名v4.1角色**。另一个工作台的70名成员加2个老师是独立名册，不能凭编号混用。
## 出场流程
1. 先验金融新闻原始来源、行情与节拍，再开始选角；遵守`../romania-market-director/references/identity-media-memory-workflow.md`。
2. 每个角色四重核对：人物编号、姓名、性别、新/老与男/女分类；矛盾立刻阻止出场。
3. 逐人读取完整JSON，包括年龄、工作、城市、投资经验、说话长度、历史立场、表达习惯及表情/GIF媒体权限；拒绝只有编号的人设猜测。
4. 助理负责自然引导，教授按现行规则只在**19:30正式晚课**出场；人物语句长短自然，避免全员附和、重复质疑、机械轮流。GIF须实际存在且许可合规。
5. 仅用户明确批准的最终稿可以生成和写入人物动态记忆；测试、草稿和待审核稿不能成为历史事实。
## 不可越线
所有群聊对白均为**虚构教学模拟**，不得冒充真实投资者、真实收益、持仓经历、客户见证或群体共识；禁止营造虚假买卖热度。
## 交付/验收
输出选角编号、完整字段一致性表、角色语气检查、素材许可与记忆状态；仍须运行`python skills/romania-market-director/scripts/validate_persona_roster.py`。测试通过不代表模拟内容可假冒真人发布。
