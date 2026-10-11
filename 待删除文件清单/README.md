# 65人项目：旧版及重复文件集中待清理清单

核对范围：本仓库 main 分支。**这里只集中列出待处理文件，没有自动移动、删除或覆盖它们。**
目前65人正式人物档案、交易中心和财经 Skill 源码均应保留。

## A. 旧版源码及随附文件（5项）

这些文件在 `legacy/005-trading/` 下，不属于当前 Python 交易中心的运行时入口：

1. `legacy/005-trading/README.md` — 旧版本说明
2. `legacy/005-trading/trading-simulator.js` — 旧的多人交易模拟代码
3. `legacy/005-trading/trade-dashboard.js` — 旧交易看板代码
4. `legacy/005-trading/tests/trading.test.cjs` — 旧版交易测试
5. `legacy/005-trading/tests/stock-chart.test.cjs` — 旧版持仓图表测试

**重要**：当前65人版本尚未证实与旧版功能完全一致。旧代码可能仍是补齐「编辑股票计划、持仓分布图、批次卖出、到期倒计时、手动持仓录入、独立每日买入名单」的参考。确认不再需要旧功能或已经迁移后再永久删除。

## B. 旧源码迁移/对照文件（3项）

6. `docs/LEGACY-TRADING-FUNCTION-PARITY.md` — 旧版与现行交易功能对照
7. `docs/legacy-trading-parity.json` — 对照记录与尚未完成的功能差异
8. `tools/test_legacy_trading_parity.py` — 要求旧源码存在的回归测试

**删除依赖**：`.github/workflows/skill-quality.yml` 仍调用 `test_legacy_trading_parity.py`；`tools/test_canonical_sources.py` 仍断言旧 JS 存在。删除第1–8项前，必须同时修改这两处检查，否则 CI 会失败。

## C. 只清理引用，不要整文件删除

- `docs/CANONICAL-SOURCES-2026-10-10.md`：包含旧项目与迁移说明，应改成纯65人来源清单。
- `docs/UNIFIED-FINANCE-SKILL-HUB.md`、`skills/romania-market-director/SKILL.md` 及部分规则和 Python 源码：存在旧人数或旧来源字样，仅改引用，不删现行业务文件。
- `README.md`：旧人数引用已于提交 `4ace8bace14a336b18c5b425de5b24e4eb73c510` 清理。

## D. 绝对保留

- `skills/romania-market-director/characters/index.json`
- `skills/romania-market-director/characters/profiles/` 中65份正式档案
- `tools/trading_65.py`、`tools/trading_65_ui.py`、`tools/trading_center_ui.py`
- `tools/finance_skill_api.py`、`tools/chennan_writing.py`
- 当前正式记忆与任何实际已保存的模拟交易账本

## 本机集中移动备查（Windows Git Bash）

下面命令**仅移动旧文件到一个审核目录**，不会永久删除；必须先处理上方 CI 依赖，再执行并测试。请在本仓库根目录运行：

```bash
mkdir -p "待删除文件_人工复核"
git mv legacy/005-trading "待删除文件_人工复核/旧交易源码"
git mv docs/LEGACY-TRADING-FUNCTION-PARITY.md "待删除文件_人工复核/"
git mv docs/legacy-trading-parity.json "待删除文件_人工复核/"
git mv tools/test_legacy_trading_parity.py "待删除文件_人工复核/"
git status
```

移动后先运行65人人物校验及交易测试，确认无部署依赖，再自行决定是否删除整个审核目录。该命令不会删除其他仓库的资料或 Git 历史。
