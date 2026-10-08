# Finance data verification — publication gate

## The seven mandatory items for EACH reported numeric market observation
1. **value / unit** — number and physically meaningful unit: points, %, bp, USD/bbl, RON/EUR, RON, shares, EUR/MWh.
2. **baseline** — unambiguous comparison target and its timestamp: prior close, previous identical publication, prior briefing, YoY, etc. If comparison impossible, `not_available`, never imply unchanged.
3. **observed_at / timezone** — observation or official effective timestamp with UTC offset and IANA timezone; webpage scrape time is separate.
4. **source_url** — link to the original item-level evidence (and publisher, dataset, observation identifier where possible).
5. **delay_status** — `realtime`, `delayed`, `end_of_day`, `unknown` and exact delay minutes *only when known*; `realtime` requires affirmative evidence.
6. **vs_previous_brief** — previous report ID, previous value, difference with signed unit, or explicit reason for unavailable comparison. Previous close is **not automatically** the previous briefing.
7. **quality/status** — `verified`, `provisional`, `unverified/omit`; record observation and publication times separately where possible.

If a field is unknown, remove the unsupported numerical claim from the publishable metrics list and report it in `coverage_gaps` with reason and next action. Do not present a loosely sourced number without a timestamp/denominator.

## Event metadata
- Headline and who did what; `published_at`, `effective_at` (or `unknown`), original timezone, source URL, `new/revised/unchanged` vs previous brief.
- Financial calendar: issuer report published time distinct from event/earnings period/ex-dividend date; sort by actual future effective date.
- Rate decisions: announcement rate, previous rate, effective date, voting details if announced. Market rumor is not an official event.

## Quality checks
- **Identity**: ticker, MIC/exchange if ambiguous, currency, share class, index type, contract delivery, data source.
- **Freshness**: latest true *data time*, source publication date, last user report time; explicitly mark stale historic snapshots.
- **Units**: `%` versus `pp` versus `bp`, millions versus absolute RON, shares vs RON volume, TTF delivery contract; do not sum incomparable units.
- **Plausibility**: percent return = `(current - baseline) / baseline * 100` when baseline !=0 and identical instrument/method, round after computing; yield spread basis points = `(yieldA_pct - yieldB_pct)*100`; index contribution only with compatible free-float weighting and corporate-action adjustments.
- **Cross-source conflict**: record both values, dates, licensing/methodology and mark `disputed`. Do not blindly average or silently choose favorable data.
- **Future dates**: no final close if market remains open; no future-mapped timestamp; account for daylight saving.
- **Previous report**: compare to most recent successfully *delivered* relevant report (not simply the previous planned timeslot), same series/units, otherwise note absence/series break.
- **Red lines**: no invented output, fabricated exact timestamps, unsourced company holdings, past returns described as guarantees, or media rumor relabeled fact.

## Data display convention
For every metric, print a trace line like:
`BET：<已核验值> 点｜基准：<上个交易日收盘值/时间>｜观测：<YYYY-MM-DD HH:mm +03:00, Europe/Bucharest>｜来源：<具体URL>｜延迟：<已核实/未知>｜较上一简报：<变化/无法对比>`

For unavailable data, print:
`BET：待核验（未获取到与当前交易日匹配的官方观测时间及数值；不使用历史快照代替）；下一步：核对BVB指数页。`

## Release severity
- BLOCK: fabricated source/quote, incompatible index, impossible dates, invalid official price attribution, falsely asserted confirmed final close.
- WARN: prior briefing unavailable, delay unknown, event effective date unknown, partial breadth universe, missing secondary confirmation; explicitly disclose.
- INFO: formatting inconsistency, minor rounding, narrative gap.

If BLOCK exists, withhold the numeric assertion and issue a data-unavailable notice. An output that is complete structurally but unsourced is **not** a successful financial brief.

## 用户固定要求：指标数值必须准确

正式资讯稿的每项指标必须从实际读取的官方原始数据或可追溯的授权行情证据核对指标身份、数值、单位、所属日期/时间、比较基准及延迟；来源链接存在、GPT自称已核验、多个转述一致或格式审核通过，都不能替代原文核对。

- 用户转发但尚未核对的数字仅放待核验底稿，并明确归属原文；不得用助理或教授口吻作为已确认行情发布。
- 保留发布者精度，不增加虚假的小数位；“超过”“约”不能改成精确值。取整或单位换算须说明，计算使用未提前舍入的原数。
- 点数、涨跌幅、百分点、基点分别计算；比较须同一指标、合约、统计范围、来源口径与时间基准。算术正确不代表输入行情真实。
- 不按点位猜指数名称；不把BET与BET-TR、纳斯达克综合与纳斯达克100混用；成交额与成交量、全市场与股票市场分开。
- 有来源冲突先隔离并解释，不取平均、不挑有利数值；旧数据明确标旧，缺项写未获取，禁止补猜。
- 发现已输出错误，明确指出旧值、更正值、对应时间与证据，并检查受影响的计算和分析，不静默改稿。

最后呈现数值＋单位＋时间＋基准＋来源＋核验状态。未知传输延迟需注明；日期型官方统计没有精确时刻时保留其日期粒度，不伪造时间，也不包装成盘中报价。
