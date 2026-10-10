# P004旧交易源码 vs 65人新版 — 功能对等性验收（2026-10-10）

**当前结论：不可删除 `legacy/005-trading/`。** 源码不被现行Python运行时直接引用，但“未被引用”并不等于“新版已包含全部旧功能”。本次核查限GitHub源码及现有测试，不代表已核实所有线上账号/历史数据。

## 已能在新版确认的流程

现行 `tools/trading_65.py::apply` 支持 `eligibility`（成员模拟开户和资金）、`create_offer`（新建股票计划）、`recommend`、`invite`、`reject`、`buy` 和 `sell`；UI中可查看持仓明细、买卖记录及只读事实快照。相关测试为 `tools/test_trading_65.py` 和 `tools/test_trading_65_api.py`。这些全部是**65人教育模拟业务**，不处理真实证券成交。

## 仍需验收／实现的旧版功能

| 模块 | 旧版实现证据 | 新版现状 | 删除前必须满足 |
| --- | --- | --- | --- |
| 已创建股票计划编辑 | `trading-simulator.js::editOffer` | 只有 `create_offer`，没有后端 `edit_offer` 操作 | 加入安全修改及相关历史一致性测试，或明确放弃此功能 |
| 按股票持仓人数图表 | `stockGroups`、`renderStockChart` | `renderHoldings` 只输出逐笔表格 | 按市场/币种/代码去重统计持有人数，绘制来自已保存持仓的图表 |
| 批次持仓与到期人员选择卖出 | `batches`、`renderBatches`、`openSellBatch` | 后端仅接受单个 `holding_id` 卖出 | 批次展示与可审计的选择性批量处理 |
| 最早可卖时间倒计时 | `remaining`、`holdingStatus` | 只有最早卖出日期及可卖状态 | 按持仓生成下一卖出节点及倒计时，随日期变化复核 |
| 手动持仓录入 | `trade-dashboard.js::openManualBuy` | 未发现等效单独录入流程 | 决定是否需要；如需要，校验身份、资金、来源后适配 |
| 独立每日买入名单／交易设置 | `generateBuyList`、`renderBuy`、`renderSettings` | 有基于股票计划的当日推荐，但不同于单独买入计划 | 检查所需行为，补齐或经用户确认弃用 |

**行为差异不可直接“照旧移植”**：旧版使用70人成员及 `db.portfolio`、`growth-workspace-db` 等前端状态，新版使用65人授权档案及本机模拟账本；编号不能直接映射。旧版资金未知时的推荐规则与新版“资金必须明确配置”不同，后者不应退化成可虚构买入。

## 删除闸门

正式记录在 `docs/legacy-trading-parity.json`。只要 `open_gaps` 未消除，`test_legacy_trading_parity.py` 就会强制保留原始两份JS源码及迁移说明。每个缺口需具备后端/UI实现、独立测试、数据完整性检查与用户同意的产品范围，才能标记为已解决。该静态闸门无法自行证明某个新功能已实现；更新此表仍需人工验收。

清理顺序：**开发分支补齐功能 → 65人身份和模拟交易回归 → 浏览器验收 → 生产版本核验 → 备份确认 → 单独删除 PR**。本次不修改真实用户数据、第三方网站、数据库或线上路由。

## 其他并行改动

UI PR #28 及图片编辑 PR #29 另行验收；尤其 PR #29 目前只嵌入原网址，并未实现编辑器源码合并或统一身份认证，不能据此删除 `trade.sasakic.cc`。
