# 给现有 GitHub 项目接入验收门禁

## 推荐工作流程

1. 在**独立 QA 分支**增加 `.quality/nuvexa-independent-qa/` 和目标应用的 `config/acceptance.json`，不触碰业务逻辑。
2. 把 `templates/.github/workflows/nuvexa-acceptance.yml` 改为适合项目的 `.github/workflows/qa-acceptance.yml`，**只在 pull_request 上运行**。
3. 建立只用于 QA 环境的账号，将 `QA_USER`, `QA_PASSWORD` 添加到 GitHub Actions secrets；不得使用真实客户资产账户；外部 PR 没有 secrets 时按 BLOCKED 处理。
4. 首次运行要看到一份明确的 `REJECTED` 报告，检查缺少的配置是否确实被拦截。
5. 修改配置和功能回归样例后，再跑一次完整测试，只有所有必需门禁 PASS 才可视为通过技术验收。
6. Settings → Rules → Rulesets → 针对 `main` 的规则，开启 required status checks（`independent-qa`）、required pull request reviews、禁止未经授权绕过。规则可用性取决于 GitHub 账户与仓库计划。
7. 用真实 GitHub 账号/团队填好 CODEOWNERS，并要求修改 `.github/workflows/` 和 `.quality/` 必须由可信审核人审查。
8. 涉及生产发布、主分支合并、DNS 与付费操作，仍遵循项目各自的独立授权流程。

## 可选叠加工具

- Skill 本身准确率：Skillgrade（https://github.com/mgechev/skillgrade）
- 第三方 Skill 安全扫描：Cisco Skill Scanner（https://github.com/cisco-ai-defense/skill-scanner）
- 安全代码审计：Cloudflare Security Audit（https://github.com/cloudflare/security-audit-skill）
- UI 规范复核：Vercel Web Design Guidelines（https://github.com/vercel-labs/agent-skills）
- 开发前验证原则：Superpowers Verification Before Completion（https://github.com/obra/superpowers）

**这些工具不是本包默认执行的一部分**；引用不代表已经安装或完成评测。需要按每个项目实际栈和权限配置。
