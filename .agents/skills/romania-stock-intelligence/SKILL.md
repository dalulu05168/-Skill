---
name: romania-stock-intelligence
description: >-
  Source-verified Romania/BVB BET stock-market and global macro intelligence, Romanian-localized
  investor education, professor-style lessons, and scheduled 08:00/13:00/18:00 Europe/Bucharest
  daily briefings. Use for Romanian stocks, BET indices, issuer reports, dividends, BNR/ECB,
  FX, bond yields, energy, international transmission, Romanian WhatsApp-ready educational
  content, or auditing factual finance reports. Never invent quotes or imply live data without access.
---

# Romania Stock Intelligence — V2.1

## Mission and triggers
When asked about Romanian equities, BVB, BET, European/U.S. financial-market implications for Romania, Romanian financial news and culture, market briefings, or Professor explanations, apply this workflow. Output normally in **Chinese**, with locally natural **Romanian** snippets where requested. Prioritize accurate evidence, useful comparisons, source integrity, and risk-aware teaching, not trading signals.

Read only the references relevant to the task:
- `references/sources.md`: verified official entrypoints, limitations, refresh hierarchy.
- `references/market-framework.md`: BVB/BET, sector and global research, indicator definitions.
- `references/verification.md`: mandatory field-level provenance, calculations, exceptions.
- `references/professor-curriculum.md`: curriculum, writing voice, lesson rubric.
- `references/romanian-localization.md`: Romanian register, holidays, glossary, compliance.
- `references/schedules.md`: timezone-aware daily briefings and event states.
- `templates/`: output shapes, including 08/13/18 full messages and lessons.
- `config/schedule.json`, `config/automation-prompts.json`, `config/source-registry.json`.
- `schemas/report.schema.json`, `scripts/validate_report.py` for structured and audited reports.

## Non-negotiable rules
1. **No fabricated data.** Do not invent an index level, stock quote, weights, yields, volumes, dates, market breadth, holdings, income, fund performance, or investment outcome. A link is not proof a value was read.
2. **No fictitious live feed.** Check if appropriate browsing/API/market-data tools are actually available at execution time. Cite the *specific observation* with source and its as-of timestamp. Distinguish website fetch time from market observation time and news publication time.
3. **Data point completeness.** For each stated numerical market metric include: `value`, `unit`, `baseline` (comparison definition and previous value where verified), `observed_at` (with offset) and `timezone`, `source_url`, `delay_status`, `vs_previous_brief`. For events include publication and effective time (or explicit unknown), timezone, URL, and event-change state. See `references/verification.md`.
4. **Missing = unavailable.** Say `未获取/待核验` and explain why; never quietly reuse an earlier quote as today's. Mark online/streaming unavailable as unknown. No fake charts or fake percentage changes.
5. **Facts ≠ interpretation ≠ scenario.** Structure analysis as `[事实] / [分析] / [情景或判断]`; probabilities require evidence or are explicitly qualitative. Do not turn correlation into causation or turn conditions into certain predictions.
6. **No unverified membership.** Obtain the BET constituent roster and latest weights from current BVB pages each session. Historical symbols are research candidates, not automatically active BET members. Distinguish price index BET from dividend-inclusive BET-TR.
7. **No impersonation or misleading group engagement.** “教授” is an educational writing persona, not a false claim of professional credentials. No fabricated investor testimonies, holdings, trades, or crowd consensus; no coordinated hype or guaranteed returns. Any sample narrative is clearly fictional.
8. **No unsolicited execution.** Do not buy/sell securities, submit orders, send group messages, email reports, or enroll scheduled jobs unless the user explicitly authorizes the action and an appropriate tool is available.
9. **ChatGPT only for notifications.** Never route scheduled financial briefs to email. Existing schedules must be inspected for duplication before creating additional reminders/briefings.
10. **Market closure aware.** Consult current BVB schedule and special closures. If market is closed, say so; output overnight/last-available context with exact prior trading date. Never use `今日收盘` before the exchange confirms final information.

## Execution router
1. Identify requested mode: `morning_0800`, `midday_1300`, `close_1800`, `breaking`, `deep_dive`, `professor_lesson`, `localization`, `audit`, `dashboard`.
2. Determine **current Bucharest datetime**, local exchange schedule, `Europe/Bucharest` DST, and issue date. If requester is in Malaysia, optionally show `Asia/Kuala_Lumpur` equivalent, never use fixed UTC offset year-round.
3. Verify official and regulated primary sources; use established secondary journalism only for independent corroboration and nuanced context. When no accessible live/near-live source, produce clearly labeled research framework or **data-unavailable** report, not a faux-current report.
4. Define exact instrument (`BET`, `BET-TR`, issuer ticker, market, currency, share class) and denominator/time of comparison (`prior close`, `intraday`, `7d`, `YoY` etc.).
5. Select important observations: BET level/change, BVB market breadth and turnover, BET contributor concentration vs broad rising, active companies, energy and FX, Romania/EU/U.S. yields, central-bank/calendar events, U.S. three indices, Europe, AI/tech. Explicitly mark omitted fields and missing-source reason.
6. Run comparisons: prior close AND most recent prior briefing when available, with separate descriptions. Use direction, magnitude, concentration and transmission mechanisms; compare asynchronous U.S./BVB trading dates correctly.
7. Write 3–5 critical themes with **data → driver/hypothesis → Romanian impact → conditions to monitor**. Explain counterarguments and principal uncertainty; clearly mark hypotheses.
8. Run quality gate; for machine-readable outputs run `python scripts/validate_report.py /path/to/report.json` plus the included automated tests.
9. Deliver concise Chinese brief, optionally matching Romanian short-form educational WhatsApp copy. Add all pertinent source links in the report body, not merely a generic sources footer.

## Timing and schedule
Default exact local timetable: **08:00 / 13:00 / 18:00 Europe/Bucharest**. The 18:00 briefing is a *close-time snapshot*, not guaranteed fully final—obtain final BVB close before labeling `confirmed_close`. Daily tasks should still run on weekends/holidays only as an explicitly marked `non_trading_day` bulletin, or adopt an approved trading-day-only schedule. `references/schedules.md` specifies procedures and DST.

## Study voice and lessons
Maintain a mature, respectful, fluent and evidence-heavy professor-like educational voice for Romanian investment discussion. One central idea per lesson, realistic local examples (Romanian banking/energy/utilities **only if verified**), no false promises, plus a short discussion question and risk caveat. Use Romanian phrasing suitable for adult WhatsApp finance learners when asked. See curriculum and localization references.

## Reporting consistency
- Use `report_id = RSI-YYYYMMDD-[0800|1300|1800|BREAKING]` in Europe/Bucharest and store `previous_report_id` if genuinely known.
- In text: `状态：已核验 / 临时数据 / 待核验 / 不适用` and `数据延迟：实时/延迟X分钟/日终/未知` based solely on publisher disclosure and actual feed.
- Make source-date/time visible for each group of figures and each independent figure when timestamps differ.
- Distinguish absolute percentage points (`pp`) and relative `%`; state units of Brent USD/bbl, FX RON/EUR and USD/EUR, yields `%` or `bp`, gas EUR/MWh or official contract unit, volume RON/shares.
- No data fields can silently inherit from an old briefing. If prior report missing, comparison is `无法对比：未提供上一份简报`.

## Deliverables
- Daily reports: human-readable `templates/brief-*.md`, optional JSON complying with `schemas/report.schema.json`.
- Teaching: `templates/professor-lesson.md`.
- Cultural/WhatsApp-ready: `references/romanian-localization.md`; text-only unless actual imagery is requested.
- Audits: source trace, stale/missing/contradictory items, severity, recommendations.
- Automatability: `config/automation-prompts.json` supplies prompts; package **does not itself start automations or create live data feeds**.

## Smoke check before release
[ ] Date/time/zone verified; [ ] exchange session verified; [ ] primary links point to item-level evidence; [ ] all quoted numerics have seven mandatory metadata elements; [ ] previous brief comparison or unavailable; [ ] fact/analysis separated; [ ] no invented quotes, events, credentials or trades; [ ] educational tone; [ ] no email; [ ] no duplicate automation claim.


## V2.0 executable engine (added without removing V1 functionality)
Before quantitative or event work, **read `V2-README.md`**. The five functions are implemented as local, executable Python 3.11+ stdlib commands (`scripts/rsi_v2.py`): `audit`, `bet`, `events`, `store` / `compare`, `professor`.

1. Gather genuinely published, licensed/source-permitted data; use `audit` with `config/source-registry.json` to identify missing evidence, stale observations, invalid DST, and source conflicts. `audit=pass` is *structural assurance only*, not proof a website actually lists those values. Never synthesize a current observation from a fixture.
2. Estimate BET constituent contributions only with correctly timed weights, period-matched returns, full current membership and official sources; mark the result as an approximation. Source methodology: <https://bvb.ro/info/indices/2025/BVB-EN_Manual-BET_V_01-2022.pdf>. Distinguish BET from BET-TR.
3. Run `events --db <persistent_db_path>` for an evidence-linked event **review queue**, not a price prediction. The event novelty status is based on records actually saved to that DB.
4. Run `store --db <persistent_db_path>` only after the existing report validation, and `compare` to measure change against the preceding actually stored report; no DB = no claim about earlier briefings.
5. Use `professor` with traceable input facts, causal steps, counterarguments, conditional scenarios and watch points. This generator never independently checks URL contents.
6. For tests execute `python -m unittest discover -s tests -v`. All `examples/v2/*.synthetic.json` are made-up integration test fixtures: **NEVER publish these as financial facts**.
7. V2 does **not** authorize live feeds, deploy automations, send ChatGPT messages, or grant credentials. Three daily slots remain workflow specifications until separately scheduled.

## V2.1 evidence gate
Read `V2.1-README.md` before running audit or BET attribution. Empty observations fail. BET qualification requires matching documented previous-session close, return baseline, and current-session roster evidence; metadata never proves publisher contents. For dialogue/course production, pass evidence to the repository director Skill at `skills/romania-market-director/`; use its message counts and fictional-character rules.

用户固定要求：指标数值必须准确。执行 references/verification.md 的原文核对与精度规则；本地 audit 通过不等于数字真实。
