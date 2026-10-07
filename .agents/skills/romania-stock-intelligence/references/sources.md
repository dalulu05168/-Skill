# Source registry — first-party evidence before interpretation

## A. Romanian core (prefer official first-party pages)

| Domain | Primary entrypoint | Intended use | Limitations / action |
|---|---|---|---|
| BVB indices | https://www.bvb.ro/FinancialInstruments/Indices/Overview | BET, BET-TR, BET-NG, BET-FI definitions and methodology | Verify the specific index, constituent refresh, dividend treatment, currency, value as-of |
| BVB index profile | https://bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx?i=BET_ | BET composition, weights, performance and observation date | Web page may show historical snapshot; verify page's visible as-of date rather than browse date |
| BVB session/closures | https://www.bvb.ro/TradingAndStatistics/TradingSessionsSchedule | opening/closing/holiday sessions | BVB may change calendar; check on each trading day, do not assume statutory holidays equal exchange holidays |
| BVB issuer event calendar | https://www.bvb.ro/FinancialInstruments/SelectedData/FinancialCalendar | earnings/AGM/dividend dates | Verify issuer IR releases and current event records; ex-date ≠ pay date |
| BVB issuer announcements | https://www.bvb.ro/FinancialInstruments/SelectedData/NewsItem | issuer regulatory filings, corporate actions | Search for precise issuer/ticker and release; generic landing page cannot evidence a particular event |
| BNR central bank | https://www.bnr.ro/ | monetary decisions, rates, FX statistics, inflation reports | Site paths change; navigate official current paths and distinguish BNR fixes from trading FX quotes |
| BNR exchange XML | https://www.bnr.ro/23988-cursurile-pietei-valutare-in-format-xml | BNR official XML data feed documentation | Verify its current XML endpoint and publication date from the BNR website; do not assume an old endpoint works or treat reference rates as tick-by-tick quotes |
| Eurostat | https://ec.europa.eu/eurostat/databrowser/ | GDP, HICP, industry, public debt, fiscal indicators | Always specify country, indicator definition, series, reference period and revision flag |
| Romania INS | https://insse.ro/cms/ | local statistical releases | Access may require navigation, official figures can be revised; do not invent inaccessible numbers |

## B. Europe, U.S. and global context

| Domain | Entry point | Intended use | Limitations |
|---|---|---|---|
| ECB EUR exchange references | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html | EUR/RON, EUR/USD daily reference | ECB reference not executable live bid/ask; publication date and time may differ from market action |
| ECB rates | https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html | monetary-policy decisions | Record released date, effective date and rate instrument |
| Fed monetary calendar | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | FOMC calendar and statements | Use decision release as source; not rumor blogs |
| Eurostat datasets | https://ec.europa.eu/eurostat/databrowser/ | real GDP/inflation/fiscal comparisons | Avoid unverified cross-country series joins |
| U.S. EIA | https://www.eia.gov/ | energy background, spot/weekly EIA reports | Series may be delayed/historical; do not label ICE/Brent settlement as EIA live |
| BVB official reports | https://www.bvb.ro/ | Romanian market and issuer data | BVB feed availability, licensing and quote delays must be checked before any automated production integration |

## C. Conditional licensed feeds / secondary corroboration
- ICE/TTF and ICE Brent: check venue licensing, quote/settlement type, contract maturity, unit and reference date. Without licensed access, do **not** fabricate gas or oil values.
- Major U.S. indices (S&P 500, Dow, Nasdaq Composite), STOXX indices and sovereign yields: verified exchange, official issuer or appropriately licensed professional vendor; record regular/extended session, close/as-of timestamp and any vendor delay.
- Yield series: choose explicit `Romania 10Y`, `Germany 10Y`, `U.S. Treasury 10Y`; never interchange primary issuance coupon, secondary market yield and auction yield. Declare maturity and curve/measurement method.
- Secondary reputable reporting may explain 'why', but report official figure's original authority; report divergent estimates as disputes, not single facts.
- No presumption that every source provides stable public API. Prefer lawful access, published usage terms and permitted rate limits; never automate bypass of anti-bot gates/paywalls.

## Evidence grading
A: authoritative issuer/exchange/regulator/central bank data with exact item URL & as-of date.
B: licensed, timestamped professional-market data with contract/field semantics.
C: quality media with attributable primary source and publication date.
D: unattributed screenshots/social claims — do not publish as fact or price.

Each source URL on a numerical item must lead to a specific observable record or explain precisely where to navigate on the official page. Website homepage as the **only** source is not proof of the data item.
