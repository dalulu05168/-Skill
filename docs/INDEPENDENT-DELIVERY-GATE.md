# Nuvexa 独立交付门禁（技术试点）

目标：任何 GPT、Codex、第三方设计/开发插件产出的版本都只算“候选”。**只有受保护 CI + 独立复核 + 仓库/部署权限规则**三者落实后，才允许称为对客户正式交付。这个方案不拦截普通 ChatGPT 文本消息。

## 当前本分支确已实现

- `delivery_gate/validator.py`：独立证据校验器。缺项、失败、未跑、跳过、版本不匹配、证据丢失/改动 → `BLOCK`，退出码 1。
- `delivery_gate/tests/test_validator.py`：正反验收测试；测试通过仅证明规则执行正确，**不代表任何客户产品合格**。
- `.github/workflows/delivery-gate-selftest.yml`：PR 静态校验门禁代码。
- `.github/workflows/reusable-delivery-gate.yml`：供其他仓库的 CI 调用，下载同一次 CI 运行产生的证据并验证提交 SHA。
- 本项目未启用自动部署、未合并主分支、未更改任何生产域名/数据。

## 必需证据

`acceptance-evidence/acceptance-report.json` 示例结构（真实通过数据必须来自运行结果；以下只是格式说明）：

```json
{
  "schema_version": 1,
  "project_id": "verified-repo/project",
  "target_sha": "40位实际PR头commit SHA",
  "checks": {
    "build": {
      "status": "pass",
      "artifact": "logs/build.txt",
      "sha256": "该日志真实SHA256",
      "executor": "github-actions/job-name",
      "command": "真实运行过的构建命令"
    }
  }
}
```

`web` 类型强制 11 项：build、unit、integration、login、navigation、ui_desktop、ui_mobile、data、security、regression、independent_review。单项不得用 `not_applicable` 绕过。实际无登录的静态网站应由独立审查确定项目类型及等价用户路径，而不是 GPT 擅自宣称已登录通过。独立审核证据必须来自不属于制作人的实际复核流程。

`service` 类型强制 8 项：build、unit、integration、api、data、security、regression、independent_review。

`content` 类型强制 4 项：sources、consistency、compliance、independent_review。

**证据不得由 AI 凭空编写！** UI 必须是浏览器实测日志、截图和缺陷复测；登录必须用授权测试账号和真实服务；数据要比对存储/API返回；2FA、支付、提款等高风险操作不得使用真实客户财产跑测试。所有日志要脱敏。

## 消费方集成方式

项目仓库的 CI 首先执行原有测试，运行浏览器端到端检查（桌面1920×1080、1366×768、手机390×844），在真实登录成功后验证菜单/路由、核心按钮、保存及刷新持久化、无横向溢出、文本不被遮挡、移动端内容完整，失败立即终止。然后由独立复核作业确认，生成 `acceptance-evidence/` 文件与 JSON，上传 `customer-acceptance-evidence` artifact。最后在**同一次 workflow**加入：

```yaml
  independent-acceptance:
    name: independent-acceptance
    needs: [real-product-tests, independent-review]
    if: ${{ always() }}
    uses: dalulu05168/-Skill/.github/workflows/reusable-delivery-gate.yml@main
    with:
      profile: web
      evidence_artifact: customer-acceptance-evidence
      approved_base_url: ${{ vars.QA_APPROVED_PREVIEW_URL }}
      allowed_host: ${{ vars.QA_APPROVED_PREVIEW_HOST }}
    secrets:
      GATE_TEST_USERNAME: ${{ secrets.QA_TEST_USERNAME }}
      GATE_TEST_PASSWORD: ${{ secrets.QA_TEST_PASSWORD }}
      GATE_TEST_OTP: ${{ secrets.QA_TEST_OTP }}
    permissions:
      contents: read
      actions: read
```

同一 evidence artifact 中还需要一份经审查的 `browser-spec.json`，例如：

```json
{
  "login": {
    "path": "/login",
    "username_selector": "input[name=email]",
    "password_selector": "input[name=password]",
    "submit_selector": "button[type=submit]",
    "success_selector": "[data-testid=dashboard]"
  },
  "routes": [
    {"path": "/dashboard", "ready_selector": "main", "expected_text": "仪表盘"},
    {"path": "/settings", "ready_selector": "h1"}
  ]
}
```

上例的CSS选择器只是演示，不一定适用于你的系统，须按真实源码维护。测试会在1920×1080、1366×768、390×844分别执行登录和必需路由，真实截图临时留在浏览器作业中，上传报告摘要而不是完整私人信息；配置未列出的页面仍然是覆盖缺口。需要2FA时，测试账号提供当前 `QA_TEST_OTP`（只通过GitHub Secrets）；缺失则阻断。必须使用隔离的合成测试用户，绝不能用客户账户；预发布地址与允许域名由受保护的工作流/变量指定，不允许使用 PR 内任意站点盗取测试密码。

如果之前测试失败，缺少 artifact，则该作业也会失败（默认拒绝），不会默默跳过。项目应把验收作业设置为 GitHub **required status check**，且有独立代码审核人。建议 pin 可审计的中央仓库 commit，防止未经审批更改门禁；例子用 `@main`，待门禁合并后才可用。

## 真正防绕过还必须做的设置（尚未实施）

1. 分项目设置 GitHub branch ruleset：强制 PR、必需 CI check、禁止管理员随意绕过、限制直接推送。
2. 独立的部署身份与 production environment protection：只接受通过验收的不可变 commit/制品，禁止外部工具直接发布旧版或未审版。
3. 将客户成品访问链接与正式发布操作放在受保护的发布作业后；不能让 GPT/第三方插件同时持有绕过 CI 的部署密钥。
4. 为每个项目配置真正的端到端测试；Playwright/浏览器截图、登录测试、接口和持久化测试必须针对**实际项目**运行。AI 生成的“PASS”文字或伪造日志不得作为验收凭证。
5. 对非 GitHub/非受控渠道（普通聊天、Canva直接分享等）无法强制拦截，只能建立统一交付入口及授权范围。

**明确限制：** 本版本验证日志文件和SHA关联，但日志“是否真由独立机器运行”仍须靠受保护 CI/审查权限保证。未经第1–4条配套措施，不能把本脚本称为全局强制阻断或真正客户验收通过。

## 快速校验

```bash
python -m unittest discover -s delivery_gate/tests -v
python delivery_gate/validator.py --report acceptance-evidence/acceptance-report.json \
  --root acceptance-evidence --expected-sha "$GITHUB_SHA" \
  --profile web --out gate-decision.json
```

如证据缺失，第二条应退出1，打印 `BLOCK`；这是预期行为。
