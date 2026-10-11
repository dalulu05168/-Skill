# 独立项目验收 Skill · Nuvexa Independent Acceptance

**状态：已打包的可运行验收工具原型（v0.1.1），不是已经部署到你所有仓库的全局拦截器。**

## 用途

针对过去遇到的：双击启动失败、白屏、登录错误、2FA/权限问题、假搜索、虚构统计、文字被截断、16:9 画面溢出、修改后未生效。采用八项门禁：`build`、`unit`、`security`、`functional`、`ui`、`auth`、`data`、`regression`。默认缺项直接拒绝交付。

## 如何安装 / 接入（必须针对每一个真实项目配置）

1. 将整个文件夹复制到该项目的 `.quality/nuvexa-independent-qa/`（不要覆盖项目原有代码）。
2. 将 `config/acceptance.template.json` 复制为 `config/acceptance.json`，填入当前系统真实启动命令、URL、按钮 CSS 选择器、功能预期、登录角色、授权测试账号与真实 API 路径。模板里的 `REPLACE_WITH...` 不可使用。
3. 安装 Python 3.11+、Playwright（`pip install playwright`，`python -m playwright install chromium`）。模型平台和云端测试可能另行收费。
4. 在另一个终端启动**真实项目**，例如 React/Vite 的 `npm run dev -- --host 127.0.0.1`。
5. 在 GitHub Actions 或独立测试环境运行：

```bash
python .quality/nuvexa-independent-qa/scripts/gate.py \
  --policy .quality/nuvexa-independent-qa/config/acceptance.json \
  --project-root . \
  --base-url http://127.0.0.1:5173 \
  --outdir qa-evidence
```

**退出码 0**：八项通过（仍需要独立截图与代码审核）。**退出码 1**：拒绝放行，包括没法测的情况。输出目录：`acceptance.json`、`acceptance-report.md`、日志、页面截图。

## 真正拦住 GPT 直接交付的条件

把 `templates/.github/workflows/nuvexa-acceptance.yml` 复制到应用项目的 `.github/workflows/qa-acceptance.yml`，根据应用修改 Node 版本、启动命令、端口、测试命令和安全扫描。将 `templates/CODEOWNERS` 的审核人占位替换成可信的 GitHub 成员/团队并放入应用仓库根目录的 `.github/CODEOWNERS` 或指定位置。

再到 GitHub 仓库 Settings → Rules → Rulesets：保护 `main`；要求这个 CI 检查必须成功；要求非作者审核，并限制绕过权限。**没有这些仓库配置，一个 Skill 文件无法强制拦截所有 AI、所有会话或所有发布。**

工作流示例配置为 `pull_request` 而不是危险的 `pull_request_target`，不会自动部署，不更改 DNS，不执行正式发布。fork PR 上没有 QA secrets 时，登录验收按缺少凭据处理为拒绝。

## 有意限制

- 这是最小可执行的独立验收骨架，不是完整 UI 视觉审美判定器。它可以查画面是否加载、指定信息是否可见、溢出、截图；是否美观需要独立人类/视觉 AI 复核。
- `data` 检查通过 UI 与 API 对照，但**不能证明 API 本身不是假数据**。金融资产和资金等关键数据还需要独立数据库/账本来源对照，以及权限隔离、审计日志与账务一致性测试。
- `security` 只是项目指定审计命令的退出码，不代表通过全面的渗透测试。
- `auth` 默认一组账户；交易系统的客户/子账户/总账户/后台权限和 2FA 必须增加定制测试。
- 每次运行从当次环境生成新报告，不会接受开发者提供的旧 PASS 报告作为本次通过依据；但项目拥有者若允许开发者修改 CI 或测试脚本，仍可能绕过，因此需要受保护分支和独立审核。
- 不在未授权环境抓取账号凭据、不绕过 2FA、不发起真实交易或真实资金操作；需要隔离测试账户与沙盒。

## 安全与第三方组件

内置两套 Python 代码为原创模板，只用标准库 + Playwright；参考上游文档，没有复制其代码。参考开源：Superpowers、Anthropic Web App Testing、Cloudflare Security Audit、Cisco Skill Scanner 和 Skillgrade。第三方许可与版本应按实际安装源单独检查。特别是 Skillgrade 的真实 AI 评测可能消耗模型调用额度。

## 独立走查表与接入说明

- `docs/INDEPENDENT-REVIEW.md`：像最终用户一样执行的人工/视觉审核清单。
- `docs/GITHUB-INTEGRATION.md`：逐仓库挂载 CI 门禁、PR 审核和发布隔离步骤。

## 当前可测试验证

```bash
python -m unittest discover -s tests -v
```

这是验收工具自身的防漏门禁测试，不是对你的真实交易平台或 CRM 验收。如果执行环境的浏览器被管理策略限制网址访问，集成测试会明确 SKIP；该部分**没有通过实测**，必须在真实 CI 重新跑。
