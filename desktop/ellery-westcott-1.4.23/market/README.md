# ELLERY WESTCOTT Desktop 1.4.23 | Index 3/3 source gate

Status: **GitHub source connectivity probe only; NOT a deployed Windows desktop fix.**
Scope: BET, BET-NG and BET-FI (Bucharest Stock Exchange).

## Sources and provenance

The Windows program's latest local candidate sources are available in the existing
1.4.23 desktop packages. The previously delivered **interface-only** update
`Westcott_Real_Three_Charts_Interface_Fix_20261025.zip` has SHA-256:

`aaafbb8bc458006283e20ab3c3144dfca7bd0db0400d9fed032e4563bbc75dd1`

This GitHub directory contains a standalone source probe and test suite. It does
**not** claim that the above ZIP's 7 application files are uploaded here,
that a BVB licensed feed is available, or that a Windows program has passed
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

Original 1.4.23 interface patch, current source ZIP and other modules are not
modified by this GitHub branch.
