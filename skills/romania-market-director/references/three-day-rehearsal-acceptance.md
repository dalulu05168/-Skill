# 连续三天新闻驱动群聊排演验收（仅财经SKILL）

## 范围与边界
- **目标**：检查新闻选题→助理解释→65人虚构教学角色的独立对白/争论→教授课程→次日历史衔接。不是另建新闻采集、通讯软件发送或交易系统。
- 三日排演只是**显著披露的模拟写作**，不是历史真实群聊或已经发布的内容。没有真实输入就标未收到，未经独立查证绝不说事实属实。
- 正式记忆与用户历史不能由模拟排演自动写入。当前 `memory/state.json` 未有已采用场景时，只能依靠**这三日排演包内部的沙盒连续性**，不能假称群成员现实中昨天争执过。

## 可执行方法
输入本地 JSON 包，结构：
```json
{
  "upstream_packet": {
    "news": [{
      "item_id": "upstream-id",
      "headline": "上游原文标题",
      "original_url": "https://example.org/original-source",
      "publisher": "publisher",
      "published_at": "2026-10-12T09:00:00+03:00",
      "event_at": "2026-10-12T09:00:00+03:00"
    }],
    "market": []
  },
  "days": [
    {"date": "2026-10-12", "scenes": [{
      "scene_id": "sandbox-d1-1", "node": "RO-08",
      "host_kind": "assistant", "news_item_ids": ["upstream-id"],
      "assistant_analysis": {
        "event": "发生了什么", "evidence_url": "https://example.org/original-source",
        "observed_at": "2026-10-12T09:00:00+03:00",
        "market_link": "与罗马尼亚市场的关联",
        "causal_path": "影响传导和前提", "counter_factors": "抵消/反面证据",
        "uncertainty": "何处尚未证实", "next_check": "下一步核查事项"
      },
      "messages": [],
      "continuity_refs": []
    }]},
    {"date": "2026-10-13", "scenes": [{
      "scene_id": "sandbox-d2-1", "node": "RO-08",
      "host_kind": "assistant", "news_item_ids": [],
      "messages": [],
      "continuity_refs": [{"scene_id": "sandbox-d1-1", "scope": "sandbox_rehearsal"}]
    }]},
    {"date": "2026-10-14", "scenes": [{
      "scene_id": "sandbox-d3-1", "node": "RO-10",
      "host_kind": "professor",
      "professor_course": {
        "course_type": "technical", "learning_objective": "今天学会什么",
        "principle": "原理", "example": "【假设】教学情景",
        "mistake": "典型误区", "practice": "一项练习",
        "next_link": "下一堂课的衔接", "source_status": "重构课纲，非遗失原稿"
      },
      "messages": [],
      "continuity_refs": [{"scene_id": "sandbox-d2-1", "scope": "sandbox_rehearsal"}]
    }]}
  ]
}
```

上述`example.org`与结构文字只是输入字段示例，**不是真实新闻，也没有经过事实核验**。正式导入需提供上游原始URL、数据原文、时间和编辑判断依据，并实际由有权访问外部来源的程序/人员交叉核查。不得因为这里存在一个合法URL而把`UNVERIFIED`自动提升成`CONFIRMED`。

成员 `messages` 每条需与65人正式档案严格匹配 `character_id/name/gender/role`、有本场唯一`message_id`、`simulation_only: true`、`text` 含`【虚构教学模拟】`、`reply_to`仅回复先前消息（或空）。语言习惯、表情、GIF权限使用现有校验器，疑似套话/反复附和产生人工审核提示。

示例执行：

```bash
python tools/multiday_rehearsal.py --input three-day-package.json --out rehearsal-review.json
python -m unittest discover -s tools -p 'test_multiday_rehearsal.py' -v
```

程序只读取三日包/65人本地档案，写一个**审核报告**（如果指定输出路径），不写正式记忆、不发布消息、不联网、不控制外部页面。

## 人工验收评分表（每项0–2分，共20分）
1. **新闻真伪与重要性**：原文、时间、变更、影响程度均实际核实；重大负面信息不因不合方向被遗漏。
2. **助理的市场分析**：说明客观事件、罗马尼亚具体传导、反向因素、风险及复核条件，而非大段念新闻。
3. **65人出场动机**：谁为什么此时说话，有兴趣或历史理由；允许沉默，不需要每节点都凑角色。
4. **人物口吻**：每人自己职业、性格、说话速度/句长、本地口语稳定，避免所有角色都用编剧口气。
5. **表情和媒体**：本人偏好与限制执行，频率贴合场景，避免每句话都有表情。
6. **独立讨论**：成员互答与原有话题可在新新闻期间交错，不围绕助理排队发言。
7. **争论可信度**：冲突围绕实质事实或解释而发生；有轻有重，不机械每天设置相同冲突。
8. **连续记忆与因果**：只能回调真正已采用场次或本次沙盒真实出现的事件，不能把草稿当历史。
9. **教授教学价值**：周一三五技术、周二四理念，19:30；讲清例子、原理、失效条件、风险和练习。
10. **全局节奏与独特性**：有新信息、有相对平静时段、有旧问题推进，避免照抄其他群的固定话术。

人工评分**不能代替事实核验，也不应作为无条件发稿许可**。对这三天的沙盒例子，只能完成代码结构与红线测试；真实新闻内容、语气与课程深度须另行审阅。

## 目前验收状态
- 三天验收的代码门禁可运行，并有测试用例。测试例子全部是虚构输入。
- 正式角色历史未导入，真实新闻推送的接口/原始文章未在本仓库得到逐条独立查验。因此不能报告“已完成真实三天排演”或“新闻真实性100%通过”。
- 上午35、下午35、晚上30（各可上下2–3）是正式内容的**弹性目标**，不是本三日测试包的硬性条数，也不是凑人设/凑争论的理由。
