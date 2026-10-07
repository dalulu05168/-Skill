# Romania Stock Intelligence Skill v1.0

**定位**：研究与教学用的罗马尼亚 / 国际金融市场情报技能包。默认中文分析、按需输出自然罗马尼亚语。

## 文件清单

```
romania-stock-intelligence/
  SKILL.md                      主技能指令（Agent Skills 结构）
  README_中文.md                 中文安装和使用说明
  GPT-QUICKSTART.md             自定义GPT/项目的调用方案
  references/
    sources.md                  官方数据源目录及限制
    market-framework.md         BET、行业、汇率、债券与国际传导框架
    verification.md             逐项数据溯源、七字段、质控
    professor-curriculum.md     16节教授课程与评分规则
    romanian-localization.md    罗语术语、语气和文化
    schedules.md                08/13/18报告和时区换算
  templates/
    brief-0800.md               早间简报
    brief-1300.md               午间盘中简报
    brief-1800.md               收盘时点简报
    professor-lesson.md         教授讲课范式
  config/
    schedule.json               时间、渠道、交易状态规则
    automation-prompts.json     三条定时任务的可复制提示词
    source-registry.json        官方数据入口登记
  schemas/
    report.schema.json          机器可读日报数据结构
  scripts/
    validate_report.py          校验时间、必需元数据、算术与链接格式
    show_schedule.py            罗马尼亚和马来西亚时间换算
    install-windows.ps1          Windows本地Codex安装脚本
    install-unix.sh              macOS/Linux本地Codex安装脚本
  tests/
    minimal_valid.json          不含行情数字的结构测试样例
    test_validate_report.py     基础自动化测试
```

## 安装到支持 Agent Skills 的 Codex/Agent

1. 解压后确保顶层文件夹叫 `romania-stock-intelligence`，其内有 `SKILL.md`。
2. 按你所用 Codex 版本的 Skills 安装规则，把文件夹放在用户技能目录（典型为 `$CODEX_HOME/skills/romania-stock-intelligence`，通常 `~/.agents/skills/romania-stock-intelligence`），或以仓库内技能方式接入。
3. Windows 用户也可在解压后的技能包目录执行 `powershell -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1`（仅首次安装；已存在则拒绝覆盖），macOS/Linux 可运行 `bash scripts/install-unix.sh`。
4. 重新载入 Codex/Agent，尝试调用：`使用 romania-stock-intelligence，做一份罗马尼亚13:00盘中分析；没有可信来源就标记待核验。`
5. 正式使用实时行情前，另行连接合法的市场数据访问方式。技能包仅提供流程、结构与校验逻辑，不含付费行情授权、BVB数据抓取器或密钥。

Codex和ChatGPT的Skills/上传知识能力并不完全相同。当前对话生成这个包不表示已自动安装进你的所有GPT对话。

## 在 ChatGPT 使用

- 打开 `GPT-QUICKSTART.md`，将其规则放到自定义GPT或项目指令里；另把 `SKILL.md` 和 `references/` 作为可读取文件供其引用。
- 需要当天行情时让它执行网页/数据源核验，并要求列出每个数值原始来源、观测时点和是否延迟。没有行情工具或未连接数据时会产生“数据缺失”的真实报告，而非虚假的行情。
- 如需自动简报，参照 `config/automation-prompts.json`，在 **支持时区的任务系统**中分别创建08:00、13:00、18:00三项任务，时区 `Europe/Bucharest`。建立前先检查已有任务，避免重复；仅允许在ChatGPT内送达，禁止邮箱。

## 快速测试（Python 3.9+、标准库，无需安装依赖）

```bash
python scripts/show_schedule.py --date 2026-10-08
python scripts/show_schedule.py --date 2026-12-08
python scripts/validate_report.py tests/minimal_valid.json
python -m unittest discover -s tests -v
```

`validate_report.py` 是**格式和自洽性检查**，并不是联网验证器，不能证明行情数值真实存在，也不能证明URL页面包含声称的数值。要发布新闻或真实行情，仍须读取并复核官方原始记录，确保页面数据时间匹配、货币单位匹配、证券/指数类型匹配。

## 立即使用的五种指令

- `使用 romania-stock-intelligence，按照08:00早报模板查询今天BVB、隔夜美股及欧元/列伊数据，逐项给原始来源。`
- `查询BVB当前BET指数构成和权重，并判断行情是否由少数高权重股推动。找不到可靠权重数据就说明。`
- `教授第1课：好公司为何不等于任何价格都值得买。罗马尼亚金融投资群口吻，中文讲稿 + 罗马尼亚语短版。`
- `审查这段财经日报每个数字是否有数值、单位、基准、观测时间、时区、链接、延迟、对前份变化。`
- `从BVB公司日历找下一个交易日的财报、除息和央行事件，只报告有时间和来源的项目。`

## 特别约束

- 不保证实时行情；BVB/ICE/交易所的数据可能需要单独授权。
- 18:00罗马尼亚当地是临近/达到常规交易日结束时点；若官方最终数据未确认，仅做临时收盘时点快报。
- 夏令时（约春至秋）罗马尼亚08/13/18对应马来西亚13/18/23；冬令时为14/19/次日00。以每年实际IANA时区为准。
- 本包不执行交易、不自动向WhatsApp发送信息、不存取个人财务账户。
- 任何示例/测试文件不包含真实今日行情；不要把测试文件当投资建议或真实报告。

**来源**：具体官方数据入口见 `references/sources.md`。首次制作时间 2026-10-08，后续指数成分、政策利率和交易日历必须每次重新核验。
