---
name: nuvexa-independent-acceptance
version: 0.1.1
description: Independent fail-closed acceptance for apps, code, UI, login, permission boundaries and real data before any claim of delivery. Run fresh commands, real browser actions, screenshots and API comparisons; reject on missing evidence. Invoke for pre-release audits, project delivery, fixed-bug verification, login failures, blank pages, ineffective searches, and skill QA.
---

# Nuvexa Independent Acceptance · 独立验收

## Mission
This skill is an **independent reviewer**, not the developer. No success claims without current-run evidence. It is not an autonomous global enforcement tool: enforcement requires each project's GitHub Actions workflow and protected branch rules.

## Non-negotiable rules
1. Inspect actual target repo/commit, requirements, test environment and app URL. Mark missing items **BLOCKED**, not **PASS**.
2. Inspect `config/acceptance.template.json`, replace every placeholder with actual selectors, routes, and commands. Missing real configuration is a failure; do not invent sample user accounts, KPIs, or passing evidence.
3. Author or inspect unit tests for key behaviors. Run a fresh build, unit tests and an applicable dependency/security audit.
4. Start the actual app using a known project-specific command, verify that the app is responsive. Use real Playwright navigation and click/fill operations, including original regression scenario.
5. Check the desktop 16:9 page (including content visibility and no-scroll if required) **and** mobile viewport. Review screenshots for typography, overlap, clipping, false placeholders, and visual consistency; code-only inspection cannot certify appearance.
6. Verify login with invalid and valid credentials, unauthorized protected data, and logout. Use only authorized test accounts, with credentials from env/secrets; never print credentials or store them in screenshots.
7. Query a real API or trusted backing source to corroborate at least one important displayed value. A hardcoded `123` never proves live data. For secure APIs, adjust authenticated test context safely.
8. For high-risk trading/admin roles, extend policy with role-specific authorization, 2FA, account segregation, transaction authorization, failure/rollback and ledger consistency tests. Baseline eight gates are a **minimum**, not full financial compliance.
9. Write `acceptance.json`, `acceptance-report.md`, logs and screenshots into a fresh run directory. Keep failed checks explicit; do not edit output to make it green.
10. **No delivery approval** unless all required gates show fresh independent evidence. In production, additionally require separate reviewer approval and GitHub branch protection. The Skill's self-attestation cannot replace an enforceable CI gate.

## Gate categories
- `build`: production build succeeds.
- `unit`: unit/integration tests pass.
- `security`: audit exits successfully; this does not prove secure code.
- `functional`: required routes, buttons and UI actions function.
- `ui`: screenshots, content visibility and specified overflow tests; visual reviewer must still inspect artifacts.
- `auth`: invalid login rejected, valid role login succeeds, protected data not exposed without login, logout works when configured.
- `data`: displayed numeric/text value equals independently retrieved API/source output.
- `regression`: original reported symptom reproduced as a passing scenario after fix.

## Execution
Run `python scripts/gate.py --policy config/acceptance.template.json --project-root PATH_TO_APP --base-url http://127.0.0.1:PORT --outdir PATH_TO_FRESH_EVIDENCE`. Requires Playwright and Chromium for web checks. Do not use template placeholders as real tests.

## Output semantics
- `PASS`: only these eight automated technical gates completed successfully for this run; **not** approval to deploy or proof every security/UI issue is absent.
- `REJECTED`: any technical check fails, blocked, or cannot run.
- Security-sensitive production deployments still require independent reviewer, approval and change-control process.

## Integrations
References (do not install/execute third-party code without source review):
- https://github.com/obra/superpowers/tree/main/skills/verification-before-completion
- https://github.com/obra/superpowers/tree/main/skills/systematic-debugging
- https://github.com/anthropics/skills/tree/main/skills/webapp-testing
- https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines
- https://github.com/cloudflare/security-audit-skill
- https://github.com/cisco-ai-defense/skill-scanner
- https://github.com/mgechev/skillgrade

## Safe deployment setup
Configure per-repository Actions status check as **required** in a branch ruleset, require one reviewer not identical to the author, and protect `SKILL.md`, QA config and workflow using CODEOWNERS. Do not enable automated production deployment without explicit user approval. For external PRs, never expose production/test secrets via `pull_request_target`.
