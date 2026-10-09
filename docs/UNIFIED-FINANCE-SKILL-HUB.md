# 罗马尼亚财经 · 统一 SKILL 工作台（第一阶段）

本仓库原有财经导演v2.3.0、新闻核验V2.1、4项增强SKILL与65人v4.1资料保持**原样独立**。新增统一入口，把这些功能按顺序串联，不再要求使用者每天重新打包/上传ZIP。

## 快速启动（本地，Windows/Mac/Linux）

需要 Python 3.11+、本仓库源码。**只需第一次取得仓库，后续在浏览器使用工作台，不需要每天下载SKILL压缩包。**

在仓库根目录执行：

```bash
python tools/finance_skill_api.py
```

浏览器打开 **http://127.0.0.1:8765/**。依次点击“检查规则及下一栏目”或“抓取BVB并生成审核包”。页面只允许本机访问，不是互联网公开部署，也不要求提供AI模型密钥。第一次运行会在当前操作系统用户目录 `~/.romania-finance-skill-hub/` 创建持久新闻候审状态和最新版报告。

没有浏览器也可以直接运行同一个执行器：

```bash
# 只检查配置、65位人物和下一栏目，不访问互联网
python tools/finance_skill_hub.py --out local-review.json

# 正式向BVB新闻RSS发起请求，并持久保留未审新闻
python tools/finance_skill_hub.py --fetch-rss --state /private-data/bvb-state.json --out /private-data/review.json

# 按当前规范的19:30导师晚课组织审核任务包（非直接生成教授真实发言）
python tools/finance_skill_hub.py --node RO-10 --out local-evening.json

# 使用用户提供的新闻候审/行情观察/模拟稿JSON一起运行
python tools/finance_skill_hub.py --input local-draft.json --node RO-08 --out local-review.json
```

Windows上的状态位置建议 `%USERPROFILE%\\.romania-finance-skill-hub`。CLI示例中的 `/private-data/` 是Linux示意路径，实际运行请替换为本机**仓库外**且可备份的路径。不要把状态/文章原文/个人数据直接提交到公共GitHub仓库。

## 统一调用的五步

| 顺序 | 实际代码与规则 | 当前能力及边界 |
|---|---|---|
| 1. 事实核验 | `bvb-fact-check` + RSI `audit_observations()` | 能检查所给的金融观察数据结构、来源域名、时间、内部冲突；**不能独立验证新闻原文或获得实时行情** |
| 2. 新闻筛选 | `news-priority` + `rss_intake` | 实际联网抓取官方BVB新闻RSS，识别待审、修订与关键词优先级；候审优先级不是已核实影响 |
| 3. 场次与助理/教授路由 | `romania-market-director` + 16节点 `schedule.json` | Europe/Bucharest夏冬令时自动选择下一栏目，教授限正式19:30课程；这里只生成编辑任务，不生成AI讲稿 |
| 4. 人物一致性 | `character-consistency` + `validate_persona_roster` | 真正读取本仓库65份完整角色档案；导入草稿会检查编号姓名性别新老身份和教授出场节点 |
| 5. 最终质量门禁 | `script-qa` + hub结构门禁 | 汇总问题并锁定对外发布；人物台词必须注明虚构教学演绎；需人工原始来源核实和最终审稿 |

所有工作流输出 `publish_status = BLOCKED_NO_AUTOMATIC_PUBLICATION`。**不调用WhatsApp、Telegram、交易接口，不模拟真实客户业绩。**

### 可选 JSON 输入

```json
{
  "news_queue": {
    "items": [
      {
        "item_id": "从真实候审队列复制",
        "digest": "从同一条候审版本复制",
        "title": "原始标题",
        "url": "https://www.bvb.ro/...",
        "urgency_hint": "routine_review"
      }
    ]
  },
  "observations": {"observations": []},
  "messages": [],
  "fictional_simulation_notice": true
}
```

所有提供的候审新闻**仍被强制视为未核实**；示例JSON中的字段值不是市场数据。未提供 `observations` 时，不运行量化事实结构审核；提供空数组会被标为无可用行情，不会生成虚拟价格。导入成员消息须带 `character_id`、`name`、`gender`、`role`、`text`；助理/教授需带 `speaker`、`text`。

## 上线前尚需完成

1. 真实的新闻原文与证券行情合法数据源的证据收集；BVB财务RSS仍隔离，异常必须显式报告。
2. 模型生成适配器（助理/教授/角色正文）、真实的罗语质量评估与审稿历史；多智能体草稿PR #1尚未合并，也没有配置生产级模型密钥。
3. 持久化后台、登录授权、外部网络部署、调度、审批流与生产安全策略。当前HTTP服务**仅绑定127.0.0.1**，未部署到任何域名。
4. 连续运行期间若不点击“抓取BVB”，没有后台定时采集；单击“抓取”只是**执行一次**联网采集，不等于新闻实时监控。
5. RSS队列 `--ack-file` 人工确认详见 `NEWS-OPERATIONS-2026-10-09.md`；本工作台保留待审版本，不提供自动审批或自动发布。

## 质量验收

```bash
python -m unittest discover -s tools -p 'test_finance_skill*.py' -v
python -m unittest discover -s .agents/skills/romania-stock-intelligence/tests -v
python skills/romania-market-director/scripts/validate_persona_roster.py
```

合并代码之前 GitHub Actions 必须全部成功；绿色代表测试通过，不代表新闻真实性或真实模型可用。
