# 005 旧交易源码（迁入 P004 · -Skill）

来源：[dalulu05168/005](https://github.com/dalulu05168/005)，2026-10-10 迁移；源码原路径 `trade-dashboard.js`、`trading-simulator.js`。本目录保留原始源码及其直接测试，不替换 -Skill 的现行交易中心。

## 文件
- `trade-dashboard.js`：旧人物交易计划、看板、持仓与卖出流程的浏览器代码
- `trading-simulator.js`：模拟股票方案、推荐、邀请、买入、持仓和卖出状态机
- `tests/trading.test.cjs`、`tests/stock-chart.test.cjs`：原项目交易规则与持仓图测试

## 隔离约束
- 源码保留旧项目的浏览器全局变量依赖（`db`、`save`、`person` 等），直接引用本目录 JS **不能**在 -Skill 的 Python 工作台独立运行；须先实现显式适配层。
- 原 005 使用 70 人角色及 `growth-workspace-db` 本地存储，现行 -Skill 使用 65 人正式档案。**不得按同编号自动映射**，不得导入旧持仓/账号到 65 人数据库。
- 现行 P004 的 `/trading`、`/skill`、新闻模块与部署参数不修改。
- 原 005 整体源码可从 [迁移前存档分支](https://github.com/dalulu05168/005/tree/archive/pre-migration-2026-10-10) 找回，清理主分支前仍须确认域名与服务已解除依赖。

## 检查
在本目录运行 `node --test tests/*.test.cjs`（Node.js 22+）。该测试仅检查旧状态逻辑；**不代表**已接入 -Skill 正式运行环境或已完成线上验收。

## 后续 P004 集成任务
1. 设计交易实体转换和65人身份校验；不迁移人物及持仓数据。
2. 将买入/卖出/推荐业务逻辑适配 `tools/finance_skill_api.py` 现有模拟交易接口。
3. 测试交易状态、库存金额/币种、买卖完整流程和页面回归，再由用户批准上线。
