# Nuvexa 编程协作框架（隔离试点 v0.1）

目标：针对已存在的 GitHub 项目，建立“读源码 → 开分支 → 编程 → 测试 → 独立验收 → 用户审批 → 部署”的固定流程。此框架**不会自动调用其他插件**，不会自动部署，也不会绕过现有验收门禁。

## 插件职责
- GitHub：真实源码、功能分支、提交、PR、检查和审核。
- Replit/Floot：仅在确认它们能读写同一项目时作为可选编程环境；禁止制造第二套无关系统。
- Context7：查证最新技术文档和版本。
- Superpowers：规划、测试驱动、调试及代码复核方法；自称测试通过不算实测。
- Supabase/Neon：按项目现有数据库选用，先看迁移和数据保护。
- Render：查看日志与部署结果；生产部署、付费或DNS修改必须先征求独立批准。
- 独立验收：沿用 .agents/skills/nuvexa-independent-acceptance 与 delivery_gate 既有证据闸门。

## 任务入口（在本仓库根目录，Python 3.11+）
1. 创建安全的待办任务：
    python -m dev_framework.orchestrator init --repo owner/project --task "修复登录白屏" --branch feat/fix-login --profile web --out /tmp/nuvexa-task.json

2. 查看任务分工（所有阶段均为 pending）：
    python -m dev_framework.orchestrator show --file /tmp/nuvexa-task.json

3. 校验任务格式（不代表业务验收）：
    python -m dev_framework.orchestrator check --file /tmp/nuvexa-task.json

4. 等真实业务测试完成，有已批准的证据包与当前提交后，调用原门禁：
    python -m dev_framework.orchestrator gate --file /tmp/nuvexa-task.json --report acceptance-evidence/acceptance-report.json --root acceptance-evidence --sha 40位当前提交 --out /tmp/decision.json

报告缺少任何必需项应返回 BLOCK。注意：hash 校验仍不能独立证明日志真的由不同人员和可信CI执行。真正发布拦截还须为各仓库配置 required checks、独立审稿者、受保护部署权限。

## 验收范围
web 必须覆盖真实构建、单测、集成、登录、导航、桌面/手机布局、数据真实性、安全、回归及独立审核。 service/content 采用原门禁中各自的必需项目。测试账号、环境变量、验证码、密钥不得写入仓库或任务清单。

## 自测（仅针对本框架）
    python -m unittest discover -s dev_framework/tests -v
    python -m unittest discover -s delivery_gate/tests -v

CI：.github/workflows/development-framework-tests.yml；不触发部署。此试点只加入编程协作代码、说明和测试，不修改新闻、人物、资金、域名或既有客户数据。
