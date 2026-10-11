---
name: p004-writer
description: P004编剧Skill。接收总导演Skill任务，依据教授、助理和65名独立人物设定创作真实自然的罗马尼亚语虚构群聊剧情，返回可审稿JSON；不接模型API或另建AI软件。
---

# 编剧 Skill

**正式名称是“编剧 Skill”，不叫“AI 编剧”。** 这是独立的写作技能指令，**不是**一个需购买API、安装Ollama或独立部署的新程序。

## 角色输入
- 总导演的 `task` 与编剧任务文字，必须和本次 `story_id/scene_id/story_date/daypart` 一致。
- 读取 `../p004-professor/SKILL.md`、`../p004-assistant/SKILL.md` 和 `../p004-members/SKILL.md`，并参考 `../p004-fiction-director/references/professor-voice.md`、`assistant-voice.md`、`member-director.md`。
- 只能使用总导演选定的新候选人，不得冒用旧65人身份。记忆仅可来自本故事 `approved_history`，不可以将试听对白或网页上的草稿当历史。
- 现实财经事实必须提供真实可检验来源；若素材是假设，台词内必须保持假设语境，不得擅自填股价、收益、已成交或已领取礼品。

## 写作任务
1. 围绕一个具体真实生活问题安排自然对话，避免全员排队回复助理或全员赞同教授。
2. 每人的句长、罗语词汇、口头禅、职业、家庭动机与当前事件联动；成员可提问、不同意、互答、讲故事或沉默。讨论有缘由，不能用机械冲突凑戏。
3. 上午/下午以助理主持为主；教授仅工作日晚间并按总导演给定课程类型出现。晚课周一三五技术、周二四理念。
4. 严格遵守已有的上下文、时间顺序。引用当场消息用 `reply_to` 指向之前的 `message_id`；引用以往历史用 `history_reference` 并来自 `approved_history`。
5. 仅返回 JSON，不包 Markdown。所有消息发言均为**虚构教学小说内容**，不得当作真实客户见证或用作欺骗性投资宣传。

## 输出结构
```json
{
  "story_id": "p004-fiction-director-independent",
  "scene_id": "来自导演任务",
  "story_date": "来自导演任务",
  "daypart": "来自导演任务",
  "lesson_type": null,
  "simulation_only": true,
  "fictional_case_only": true,
  "status": "DRAFT_NOT_ADOPTED",
  "approved_by_user": false,
  "publishable": false,
  "messages": [
    {"message_id":"m01","speaker_id":"assistant","text":"Exemplu ipotetic, nu o cotație reală."}
  ]
}
```

`lesson_type` 必须原样复制导演任务的 `technical/philosophy/null`，台词 `speaker_id` 必须来自导演本场允许名单（另允许助理、合规的晚间教授）。当稿件被退回时，只按 `blocking_issues/rewrite_instruction` 修改并重新交导演审核；**编剧不得自行把草稿标成正式采用**。
