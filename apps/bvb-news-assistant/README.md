# BVB information collector v5 repair

Standalone repair of the uploaded Windows news desk; not the repository's legacy finance hub. It does not use this repository's characters, trading ledgers or memory. All schedule times are Europe/Bucharest. First collection is 15 minutes before each of the 12 nodes; external nodes also update at the node, with N05 supplement at 10:05. Evenings reuse supplied/cached material. Collection retrieves what the source returns at request time; a selected node is an organizational label, not a historical market query.

## Start and use
Extract the entire ZIP. Close the old server and run `启动_BVB资讯助手.cmd`. Keep the terminal, browser and computer running. Enable scheduled collection, or choose a node and click manual collection. Import additional metrics and paste adopted conversation/course questions in the context box. Export the node JSON/TXT for the director Skill. Export daily records before clearing browser data.

The program requests priority media before official RSS sources. Economica and Romania Insider use public RSS. Profit has general RSS plus the requested political section's public headlines; those are editorial candidates, not political discussion permission. Bloomberg, Reuters and WSJ use only their ordinary public pages; restrictions are reported rather than bypassed. HTTP success is not article/financial truth verification.

## Repairs
- All seven requested media now have real request paths, not just visible links.
- Missing TTF contract data clears price-dependent fields in backend and exports, including older imported missing data.
- Each node keeps its own news, reference metrics and BET quote snapshot; subsequent collection cannot overwrite older node values.
- Export time, collection completion and per-source/metric observation times are distinct. The live/current cache without a node snapshot is explicitly labeled.
- Prior-session index references are not automatically declared stale just because a weekend elapsed; exact session validity remains subject to market-calendar review.
- Today’s missed tasks after sleep/reload are recovered with persistent scheduler cursor and delayed labels. Recovery fetches current material, never invents old observations. No overnight/previous-day backfill and no collection while the app is closed.
- Treasury yield changes include basis points; prior daily close is preferred over a potentially multi-day range baseline.
- Newly allowed source domains remain exact HTTPS allowlisted; XML DTD/external resolution prohibited. Invalid sources have explicit errors.
- Reviewed original excerpts survive unchanged RSS refreshes; changed articles invalidate prior review.
- Longer refresh timeout accommodates serial source requests. Optional title translation remains opt-in.

## Evidence and remaining external constraints
See `tests/evidence/http-live.json`: real local PowerShell 7.6.6 HTTP calls and public-source results. `browser.json` and screenshots are explicitly simulated API browser regression; not proof of live market accuracy. Source responses can change with time and network location.

The live round returned 94 candidate entries across 8 successful source paths. BVB RSS returned 500; Bloomberg returned 403; Reuters 401; WSJ was blocked by the network proxy. These are not disguised as successful ingestion. Without authorized real-time providers, five-level order books, tick trades, exact opening 5-minute statistics, full official economic calendars and verified TTF contracts remain unavailable and must be imported. Final closing snapshots require another collection/import after official values form. Official holiday/session identification is not automated. Automatic truth verification is not claimed.

## Reproduce checks
- `node tests/core.test.cjs`
- `node tests/regression.test.cjs`
- `powershell -NoProfile -File tests/server.test.ps1` (Windows fixture checks, no live financial claims)
- Install Playwright separately for development, then `node tests/browser.test.cjs`; set `PLAYWRIGHT_MODULE`/`CHROMIUM_PATH` if necessary. No Node/Playwright dependency for end-user Windows startup.

The isolated CI workflow checks Windows PowerShell 5.1 and browser regressions. CI status must be inspected; its existence does not imply it has run. No production deploy/merge performed. Independent acceptance and an actual uninterrupted trading-day run remain outstanding; this is a review candidate, not an independently accepted production release.
