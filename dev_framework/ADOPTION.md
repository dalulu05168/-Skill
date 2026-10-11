# Nuvexa 项目接入说明（第二阶段，待审核）

## 已发现的缺口（2026-10-11 快照）

对以下两个仓库的 GitHub Branch API 实时检查显示：`main.protected = false`、必需检查为空、rulesets 为空。

- `dalulu05168/-Skill`
- `dalulu05168/growth-story-workspace`

因此之前的 GitHub Actions 通过只证明测试作业成功，**不能**证明“必须通过测试才能合并”，也不能证明独立审稿或正式发布受控。

### 审查命令（仓库根目录）

以有权限的 GitHub API 实际响应保存 `branch.json`：

```bash
gh api repos/OWNER/REPO/branches/main > branch.json
python -m dev_framework.governance_audit --repo OWNER/REPO --branch main --input branch.json --out governance-decision.json
```

- `BLOCK`：缺失保护或强制 CI；阻止使用“已具备不可绕过验收”措辞。
- `PASS_BRANCH_CHECKS_ONLY`：仅证明**这个快照**显示分支保护和强制状态检查；不是应用验收通过。仍要查规则集管理员旁路、独立 Reviewer 与生产环境权限。
- 输入 JSON 可能被伪造，真正的执行应在可信 CI 中从 GitHub API 读取，不能接受开发者提交的静态“通过快照”。

### 真实业务项目接入顺序

1. **安全试点**：在独立分支新增仅适用于 PR 的 `source-preflight`，执行当前项目实际 `npm ci`、`npm test`、`npm run test:gate`、`npm run build:static`。这只验证源码、构建和单测，**不代表真实登录/数据/手机端已验收**。
2. **分支审计**：在同一 PR 中从 GitHub API 读取 `main` 的真实保护信息，调用中央 `dev_framework/governance_audit.py`。未保护应如实标红 `BLOCK`，不是测试失败的假问题。
3. **完整验收**：准备受审查的真实端到端测试、合成测试账号（Secrets）、预发布 URL/域名、审稿人、证据 artifact。每次真实测试与独立复核关联同一 PR commit SHA。
4. **连接中央门禁**：受保护的调用方 workflow 在真实测试与独立复核作业结束后，调用 `.github/workflows/reusable-delivery-gate.yml`。只有业务项目的访问域名、路线、测试账号、环境和可信证据都可用时才启用，不允许造假 PASS。可使用已审核且固定的中央代码 commit SHA，而不是未受控的可变分支。
5. **合并与发布保护**：单独征得用户授权，设置 GitHub branch ruleset（强制 PR/required status checks/独立审核和禁止旁路）及生产环境独立权限。逐项目确认，不自动改所有仓库。
6. **正式部署**：必须再次取得用户独立批准；Render、DNS、付费资源均保持未操作。

### 财经相关项目的特例

news/content gate 和 Web 登录界面的必需证据不同，`content` 必须核验新闻原始链接、发布时间、中文编写质量和数据。金融/交易后台需增加账户/权限/2FA/审计轨迹及资产数据一致性测试。不能拿模拟交易记录当真实投资业绩。各项目保留自身独立数据、人物及业务规则，不被此协调框架重置。

### 当前禁令

- 不合并 `main`、不部署、不改 DNS、不产生费用。
- 任何开发者或 AI 编写的静态 `acceptance-report.json`，都不等于真实证据。
- 不用中央框架测试替代各项目真实登录、实际 UI 页面操作和数据库回读。
