# Daily briefing rules — timezone and delivery semantics

## Authoritative timetable
- `Europe/Bucharest`, exact schedule at **08:00**, **13:00**, **18:00**, every local calendar day unless user requests exchange-session-only.
- ChatGPT task notifications/in-chat content only; **never email**. Only actual connected/available scheduling tool can turn prompts into working tasks. Merely installing Skill files does not schedule or fetch data.
- Morning purpose: BVB preopen preparation, overnight U.S. close, European morning context, announced Romanian agenda. Label previous session close, never represent as open-market live price.
- Midday purpose: current BVB session breadth, turnover, intraday developments as verifiably published, emerging earnings/news, international risk changes.
- 18:00 purpose: BVB close-time **snapshot** and events. Official BVB regular session's closing trading phase runs until 18:00. If verified definitive prices not yet posted at 18:00, report `临时/待确认` rather than `最终收盘` and track later revision if automation exists.
- Closed days: replace 'trading now' with `非交易日`; use prior session as-of and give verified macro/calendar/education update. On weekends, 13/18 briefs should not imply live BVB changes.
- Missing source: publish a source-status bulletin with missing items rather than fake figures.

## DST examples (not fixed offsets)
Romania summer time EEST = UTC+3, Malaysia MYT = UTC+8; morning 08→13:00 MYT, midday 13→18:00 MYT, evening 18→23:00 MYT **same date**.
Romania winter time EET = UTC+2, Malaysia MYT = UTC+8; morning 08→14:00 MYT, midday 13→19:00 MYT, evening 18→00:00 MYT **next calendar day**.
The time zone should be handled via IANA timezone conversion (`zoneinfo`/scheduler tz-aware rules); never schedule fixed MYT hours for the entire year if Romanian time is the controlling schedule. A separate older Malaysia-time 12:40 daily reminder was previously discussed; do not silently substitute it for the newer explicit 08/13/18 Romanian schedule or create a duplicate task.

## State machine
`SCHEDULED → SOURCES_CHECKED → VERIFIED / PARTIAL / UNAVAILABLE → DELIVERED → REVISION_IF_REQUIRED`.
- On delivery, record `report_id`, produced_at timezone, `previous_report_id`, observed figures, official sources and completeness. Do not assert delivery occurred unless a delivery system confirms.
- Material correction: identify changed field, old/new values, cause, original and correction times, issue `更正` note; do not silently overwrite historical report.
- News deduplication: fingerprint using source URL+headline+event time; only re-report if material new facts or changed market implications. Label `新增 / 修订 / 未变`.
- Previous report comparison: look up most recent successful delivered report. If no accessible prior report, mark `无法对比` for each quantitative metric or aggregate field.
- During temporary data failure: one partial briefing, not repeated stale observations masquerading as updates.

## Task prompts
Use `config/automation-prompts.json`. A scheduler must use timezone `Europe/Bucharest`, not the current Malaysia offset. If automation tool cannot honor IANA timezone, schedule through timezone-capable scheduler or maintain seasonal adjustments only after approval. Inspect existing task automations for same scope before creating duplicates.

## Quantitative reporting defaults
Cover selected measures only if accessible and verified: BET price and change, component breadth, concentration, liquid names, Brent, Dutch TTF, EUR/RON, EUR/USD, Romanian/German/U.S. yields, BVB upcoming events, S&P 500/Dow/Nasdaq/selected European indices. No implied service-level guarantees of 08:00 fresh official statistics.
