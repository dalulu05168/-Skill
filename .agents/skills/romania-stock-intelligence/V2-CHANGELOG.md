# V2.0 / 2026-10-08

## 新增

- `rsi_core/common.py`：结构、时间/时区、证据 URL、有限值强校验
- `rsi_core/quality.py`：可追溯观察值、时效、矛盾检查；不将格式校验冒充事实认证
- `rsi_core/bet.py`：BET 个股归因*估计*、涨跌广度、权重覆盖、差异标记
- `rsi_core/events.py`：透明、非预测性的事件审查优先级及更新状态
- `rsi_core/storage.py`：可持久化 SQLite、不可覆盖报告、历史真实差异、事件去重
- `rsi_core/professor.py`：证据驱动教授课堂，强制反论点与三情景
- `scripts/rsi_v2.py`：统一 CLI
- `examples/v2/`：明确标记的合成测试样例
- `tests/test_v2.py`：含错误处理、跨时区、CLI 端到端与历史一致性测试
- `V2-README.md`：执行命令、数据合同、真实能力与局限

## 兼容性

保留 V1.0 的运行器、报告格式、课程、自动日报规则与其他已有仓库文件。该增量版不启用任何不经用户许可的外部数据源、群发或调度。
