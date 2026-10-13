# P004 65人交易中心 · 免费独立部署

- **GitHub 分支：** `fix/trading65-full-flow-20261013`，PR #48，暂不合并正式主分支
- **Render：** Free Python Web Service，Singapore，启动 `python tools/trading_65_server.py --host 0.0.0.0 --port $PORT`
- **构建：** `pip install -r requirements-trading-free.txt && python -m compileall -q tools`
- **Neon：** Free Postgres，独立项目 `nuvexa-p004-trading65-free`，Singapore
- **环境变量（只放 Render Secrets，严禁提交到 GitHub）：** `P004_TRADE_DATABASE_URL`、`FINANCE_ACCESS_USER`、`FINANCE_ACCESS_PASSWORD`（≥16字符）、`FINANCE_REQUIRE_DURABLE_STORAGE=1`、`PYTHON_VERSION=3.11.11`
- **健康检查：** `/healthz`（会检查 PostgreSQL）
- **首页：** `/` 转到 `/trading`，公开访问必须提供 HTTP Basic Auth 登录
- **安全隔离：** 只开放65人交易记录、持仓、模拟账户和正式人物资料只读接口；不会开放 RSS 准备、AI 内容发布、记忆写入及其他无持久化模块。
- **持久化：** `trading_65_storage.py` 使用单独的 `p004_trading65_ledger` PostgreSQL JSONB 表，仅接受更高一版 revision，过时请求会报错；数据库不可用时绝不回退写入 Render 临时文件。
- **原本本地运行：** 没有 `P004_TRADE_DATABASE_URL` 时，维持旧版 JSON 文件模式，不要求数据库。
- **原始账本迁移：** 不自动导入旧 70 / 72 人或未知本地账本。若有原有65人真实模拟记录，先人工确认和备份，再执行专门迁移（当前部署使用全新空账本）。

## 免费服务限制

1. Render Free Web Service 15分钟无人访问会休眠，再打开通常需冷启动；每月免费实例时数、带宽和构建额度有限；超过额度时可能暂停或产生额外费用（取决于 Render 账号付款设置）。不允许自动升级付费。
2. Neon Free 数据库按其免费套餐资源限制提供服务，数据不能替代独立备份。定期导出账本仍有必要。
3. Render Free 的本地文件随休眠或重启丢失，*除了交易中心持久化到 Neon 的账本外*，不应将新闻/人物会话文件存储于该服务。
4. HTTP Basic 登录属于有限防护，必须 HTTPS，后续正式生产仍需角色权限、登录审计、限流、备份和灾备。此免费方案仅供小规模模拟交易中心验收。
5. 不会把模拟交易数据称为真实市场订单或实盘成交。

## 验收项目

- 未认证的 `/trading`、`/api/trading/sim/state`、`/api/trading/sim/action` 拒绝访问
- 授权后的正式65人名单完整、拒绝旧70/72人资料
- 65人模拟开户设置保存后重启仍保留；股票计划、推荐、邀请、买卖及持仓按现有逻辑形成可追溯模拟记录
- 写入并发版本冲突拒绝覆盖
- 故意断开数据库时 API/页面失败提示，绝不伪报成功
- 桌面/移动浏览器实际点击测试（TinyFish）
- 不改变 `invest.sasakic.cc` 旧静态预览的 DNS，先在 Render 独立默认域名验收。
