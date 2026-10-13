# PROJECT-CATALOG｜仓库项目分区

**重要：本仓库的 `romania-market-director/characters` 65人不是 ELLERY WESTCOTT 最新65人。**
ELLERY WESTCOTT 的唯一人物来源在 [Westcott-Intelligence](https://github.com/dalulu05168/Westcott-Intelligence/blob/main/skills/p004-chat-suite/characters/final-identity-65.json)，**禁止把这里的同编号人物当作 Westcott 人物**。

## 本仓库实际项目模块

| 项目分区 | 资料归属（现有工作路径） | 处理边界 |
|---|---|---|
| RO-FINANCE-LEGACY（旧罗马尼亚财经工作台） | `skills/romania-market-director/`、其他 `skills/`、`.agents/skills/romania-stock-intelligence/`、`tools/finance_*`、`tools/trading_65*`、`tools/chennan_*`、相关 `docs/` | 旧版独立系统；**不再作为 Westcott 人物来源**，当前程序仍读取旧65人JSON，删前须拆除依赖 |
| NUVEXA-ACCEPTANCE（独立验收工具） | `delivery_gate/`、`.agents/skills/nuvexa-independent-acceptance/`、`docs/INDEPENDENT-DELIVERY-GATE.md` | 验收工具与交易业务数据分离 |
| LEGACY-005（隔离的旧交易代码） | `legacy/005-trading/`、`docs/LEGACY-TRADING-FUNCTION-PARITY.md` 及其测试 | 不是线上入口；部分CI仍引用，按既有待清理清单核实 |
| THIRD-PARTY（第三方只读研究资料） | `third_party/` | 保留许可来源，不作为本地项目代码或正式人物资料 |

## 统一存放规则
1. 每项新项目明确项目ID和唯一GitHub仓库；同项目的源码、人物、素材、文档、记忆、测试都归到对应项目目录，不许跨项目拼接。
2. 相同文件只允许一个**正式源**；旧版本标明 archive/legacy，不以历史文件冒充最新。
3. 当前旧目录仍为程序真实路径，不凭目录名更改运行依赖；迁移需同步修复引用、CI、部署和数据读取，并核对测试后才能清理。
4. 任何新65人表、人物身份更新属于 `Westcott-Intelligence`，不得写入本仓库旧65人目录。
5. 删除候选范围查 `待删除文件清单/README.md`。本次分类登记**不删除**程序还在使用的正式数据或交易账本。

## 其它仓库
- [ELLERY WESTCOTT 正式65人与五Skill](https://github.com/dalulu05168/Westcott-Intelligence)
- [Brantone Veylor CRM](https://github.com/dalulu05168/-)
- [桌面教程](https://github.com/dalulu05168/desktop-tutorial)

本文件登记的是目前真实位置，不虚称已完成物理搬迁或已修改生产部署。
