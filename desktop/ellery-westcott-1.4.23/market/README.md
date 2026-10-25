# ELLERY WESTCOTT Desktop 1.4.23 | Index 3/3 source gate

Status: **GitHub source connectivity probe only; NOT a deployed Windows desktop fix.**
Scope: BET, BET-NG and BET-FI (Bucharest Stock Exchange).

## Sources and provenance

The Windows program's latest local candidate sources are available in the existing
1.4.23 desktop packages. The previously delivered **interface-only** update
`Westcott_Real_Three_Charts_Interface_Fix_20261025.zip` has SHA-256:

`aaafbb8bc458006283e20ab3c3144dfca7bd0db0400d9fed032e4563bbc75dd1`

This GitHub directory now contains all seven interface-patch application source
files under `src/` (intraday.py, market_data.py, canva_market.py,
chart_draw.py, bridge.py, market.html, market.js), plus actual provider
probe and tests. `src/intraday.py` is the corrected 2026-10-25 SOAP 1.1
version; the other six are the original patch sources.
This does **not** mean the complete Windows EXE/release/assets are hosted here,
that data licensing is guaranteed, or that a Windows installation has passed
live end-to-end verification. Keep P004 legacy 65-member data separate.

## Actual probe

The endpoint is the official BVB delayed service:
`https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx`, operation
`IndicesDataSeries`, separately for BET, BET-NG and BET-FI.

BVB documents this operation as providing the last trading session's index
observations, updated approximately once per minute. The documented
description **does not itself prove the endpoint is currently accessible**.

```sh
python -m unittest discover -s desktop/ellery-westcott-1.4.23/market -p 'test_*.py' -v
python desktop/ellery-westcott-1.4.23/market/bvb_index_probe.py --output build/market-bvb/evidence.json
```

Offline tests use synthetic XML fixtures and never represent live quotations.
The network probe calls BVB directly and writes timestamp, source, instrument,
number of matched observations, market session date and failure reason per index.
A 3/3 pass requires >=2 actual matching observations for each of three codes.
On 2026-10-25 GitHub run 40148470034 retrieved 1,296 BET,
968 BET-NG and 84 BET-FI **actual historical** points (2026-10-23 session).
The official GetIndex quotes also matched each series' last price exactly.
BVB's SOAP 1.1 POST worked; ordinary GET and form POST returned HTTP 500.
The Windows intraday source now uses the verified SOAP protocol.
A successful Sunday probe is **history connectivity**, not proof of timely
Monday open prices.

## Still required before claiming the user's request is complete

1. Run the real-source probe from GitHub-hosted runner and inspect uploaded evidence.
   If it fails, confirm exact BVB authentication/parameter/response schema.
2. Reconcile the actual XML structure against the Windows
   `payload/resources/modules/market/intraday.py` parser.
3. On a market-open day, click **获取数据** once on a selected template and verify
   each of the 3 labelled price series has the correct symbol, source and
   current market timestamp. No made-up values or interpolated bars.
4. Verify the three real price lines appear in the current template, 4K PNG
   export contains those same lines, and rise is green `+` / fall is red `−`.
5. Only then merge or distribute a Windows installer. No credential in repo.

The GitHub branch is a draft PR, not a production deploy. Updated Windows
source for intraday.py is also available as a separate one-file update ZIP
`Westcott_BVB_SOAP_Real_ThreeCharts_20261025.zip`
(SHA-256: `585c811be1ab8982865c39de77eaa5756cf52d2fe7ed5698b98f17d370435149`).
The ZIP does not modify template images or other application modules.
