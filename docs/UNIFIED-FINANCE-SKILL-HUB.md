# 罗马尼亚财经 · 统一 SKILL 工作台（第一阶段）

本仓库原有财经导演v2.3.0、新闻核验V2.1、4项增强SKILL与65人v4.1资料保持**原样独立**。新增统一入口，把这些功能按顺序串联，不再要求使用者每天重新打包/上传ZIP。

## 快速启动（本地，Windows/Mac/Linux）

需要 Python 3.11+、本仓库源码。**部分Windows电脑还需要一次性安装IANA时区数据：`py -3 -m pip install tzdata`。** 启动脚本会检测并明确提示，不会自动下载安装或无声退出。**只需第一次取得仓库，后续在浏览器使用工作台，不需要每天下载SKILL压缩包。**

Windows可以在仓库目录直接双击 `START-FINANCE-SKILL.cmd`；该脚本使用已有的Python启动本地服务，成功绑定后自动打开浏览器。没有Python或缺少罗马尼亚时区数据时，黑色命令窗口会保留错误提示，不会偷偷下载软件。\n\n在仓库根目录执行：在仓库根目录执行：

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


## 交易中心并入同一工作台（65人人物，独立模块）

首页导航增加「✍️ 交易中心」，本机路径为 `http://127.0.0.1:8765/trading`。两模块共享一个本地服务，写作和新闻各走自己的API/业务流程；**不是用旧独立72人网站的iframe冒充合并**。

- **统一人物来源：**每次写作任务都通过 `validate_persona_roster.validate()` 校验65份全量人物档案和索引，并直接读取每个人的姓名、性别、新老标签、职业、语言DNA、表情与媒体规则；额外的70/72号角色被拒绝；相同编号的其他项目历史禁止导入。
- **保留原话：**提供助理或教授原文、话题、日期、课程节点和人物选择。教授只有在 RO-10 节点允许选择。网页输出包含完整人设的结构化提示词；**不声称由本机自动生成台词**。
- **草稿门禁：**AI输出由用户手动粘贴JSON。先核查人物ID/姓名/性别/新老、是否来自本轮名单、禁用表达、回复引用，再由用户确认正式采用。结构通过不意味着自然语言正确或事实经过核实。未确认的草稿不会进入正式历史。
- **文档与历史：**可以新建/修改文档，查看正式采用会话，最近5场已采用会话随下一份提示词提供给AI作连续性参考。写作不更改新闻RSS候审队列；新闻仍需人工事实核验和发布审批。
- **存储：**本机 `~/.romania-finance-skill-hub/chennan-writing-65.json` 原子写入；原新闻文件 `bvb-news-review-state.json` 和 `latest-internal-review.json` 不迁移、不覆盖。清除本机写作目录可能丢失未备份资料，请自行备份；不提供云端同步、用户登录或跨电脑同步。
- **原项目状态：**原72人独立网站及 Supabase 72人历史保留原样；本次合并不提供自动72→65人映射、不继承交易模拟、人物资产、旧账号或在线数据库，避免错误混同。

运行验证：

```bash
python -m unittest discover -s tools -p 'test_chennan_writing.py' -v
python -m unittest discover -s tools -p 'test_finance_skill*.py' -v
python skills/romania-market-director/scripts/validate_persona_roster.py
```

API：`GET /api/trading/people`、`GET /api/trading/profile?character_id=01`、`GET /api/trading/state`、`POST /api/trading/prompt`、`POST /api/trading/validate`、`POST /api/trading/adopt`、`POST /api/trading/docs`；本地监听仍限定 `127.0.0.1`，不公开公网部署。
