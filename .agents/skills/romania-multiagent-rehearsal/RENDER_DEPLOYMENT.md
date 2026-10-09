# Render server staging runbook

## Deployment status
This is the **read-only stage-0 bootstrap service**, not an enabled model service and **not** a WhatsApp sender. The branch must not be merged or deployed to production without separate confirmation and review.

## Recommended Render configuration
- Workspace: ask the user to explicitly confirm the Render workspace shown by the connector; never choose an account/workspace by guessing.
- Type: Web Service; runtime: Python; plan: `free` for bootstrap **if the account supports it**. Free instances may sleep and their disks are ephemeral.
- Repository: `https://github.com/dalulu05168/-Skill`
- Branch: `feature/romania-multiagent-rehearsal-v1-3-20261009`
- Region: Frankfurt for proximity to Romania (user may override).
- Auto deploy: **no** on review branch.
- Build command:
  `python -m compileall -q .agents/skills/romania-multiagent-rehearsal/scripts && python -m unittest discover -s .agents/skills/romania-multiagent-rehearsal/tests -v`
- Start command:
  `python .agents/skills/romania-multiagent-rehearsal/scripts/server.py`
- No environment keys are needed for this bootstrap. No API keys in source control or logs.

## Safe endpoints
- `GET /healthz` 200 only when the existing 65 persona files are readable; signals the **bootstrap only**.
- `GET /readyz` 503 until required LLM packages and a model key are present; does **not** authorize generation.
- Everything else: 404.
- No POST, WhatsApp send, public AI generation or customer-management endpoints.

## Persisted memory
The local SQLite in the rehearsal CLI is *temporary* on an unmounted Render instance. Do **not** count on a free Render service filesystem to keep memories across deploys or restarts. For real role memory, choose a persistent Postgres-backed or compatible Mem0 memory store after capacity/privacy review, approval and secret provisioning.

## Stage-1 (requires further approval)
1. Provision an isolated private service/runner and persistent memory store.
2. Set `OPENAI_API_KEY` (or Azure provider credentials) only in Render's secret environment-variable controls.
3. Install/version-lock TinyTroupe, Mem0 and CrewAI in a dedicated runtime.
4. Run 3 genuine internal model calls; independently review Romanian localization, character identity and financial-source validity.
5. Keep human approval as a separate step. Never present imaginary persona posts as authentic investor experiences.

## Existing schedule
Never create duplicate market-briefing cron jobs; the current user schedule remains `07:00/12:00/17:00 Europe/Bucharest` and the evening professor education curriculum remains Mon/Wed/Fri technical and Tue/Thu investment philosophy, at 20:20 local.

## Verification
Run GitHub Actions `Romania multi-agent offline tests`; passing this workflow proves schema/isolated-memory/health checks, not remote model readiness.
