"""Local-first template composer linked to the 65-person simulated trading ledger."""

PAGE = r'''<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>交易图片与战绩 · NUVEXA</title>
<style>
:root{font-family:Inter,"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;color:#26313e;background:#f5f7f9}
*{box-sizing:border-box}body{margin:0;background:#f5f7f9;color:#26313e}.app{max-width:1600px;margin:auto;padding:22px clamp(14px,2.2vw,34px) 46px}
h1{font-size:clamp(23px,2.3vw,32px);margin:18px 0 7px;color:#17283b}h2{font-size:17px;margin:0 0 12px;color:#26394c}p{margin:0;color:#647282;line-height:1.65}
.head{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.head p{font-size:13px}.badge{display:inline-flex;border:1px solid #d7e0e9;background:#f3f7fb;color:#34526f;padding:6px 10px;border-radius:99px;font-size:12px;font-weight:700}
.notice{margin:14px 0;padding:12px 15px;border:1px solid #e5dcc7;background:#fffdf8;border-radius:10px;color:#66552e;font-size:13px;line-height:1.65}
.card{background:#fff;border:1px solid #e2e7ed;border-radius:12px;padding:17px;min-width:0;box-shadow:0 3px 12px #18283a08}.top-grid{display:grid;grid-template-columns:minmax(300px,.72fr) minmax(0,1.6fr);gap:14px;align-items:start}.stack{display:grid;gap:14px}.field{display:grid;gap:6px;margin:11px 0}.field>span,.field label{font-size:12px;font-weight:700;color:#566576}.field input,.field select,.field textarea{width:100%;min-height:40px;padding:8px 10px;border:1px solid #d6dee7;border-radius:8px;background:#fff;color:#26313e;font:inherit;font-size:13px}.field textarea{min-height:92px;resize:vertical}.field input:focus,.field select:focus,.field textarea:focus{outline:2px solid #7899ba;outline-offset:1px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.button,.button-secondary,.button-link{display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:39px;border:1px solid #213a55;border-radius:8px;padding:8px 12px;background:#193653;color:#fff;text-decoration:none;font:inherit;font-size:12px;font-weight:750;cursor:pointer}.button-secondary,.button-link{background:#fff;color:#30465d;border-color:#d2dae3}.button:disabled{opacity:.5;cursor:not-allowed}.button:hover{background:#102a45}.button-secondary:hover,.button-link:hover{background:#f3f6f8}.hint{font-size:11px;color:#778493;line-height:1.6}.status{margin-top:9px;min-height:22px;font-size:12px;color:#596a7b}.file-input{display:block;width:100%;padding:10px;border:1px dashed #bcc8d5;border-radius:9px;background:#fafbfd;font-size:12px}
.canvas-wrap{min-width:0;border:1px solid #dce3eb;border-radius:10px;background:#101a26;padding:10px;display:grid;place-items:center;min-height:300px;overflow:hidden}.canvas-wrap canvas{display:block;width:100%;max-height:72vh;object-fit:contain;touch-action:none;background:#f1f3f5}.canvas-empty{padding:40px 15px;text-align:center;color:#d2dbe5;font-size:13px}.section-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}.section-head h2{margin:0}.subnote{margin:-2px 0 11px;font-size:11px;color:#788594}.statsline{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:9px}.stat-chip{padding:6px 9px;border:1px solid #e3e8ef;border-radius:8px;background:#fafbfd;font-size:11px;color:#536274}.pager{display:flex;align-items:center;gap:8px}.hidden{display:none!important}
#chartHost{position:fixed;left:-10000px;top:0;width:1600px;height:744px;overflow:hidden;pointer-events:none;background:#fff}.chart-source{font-size:11px;color:#778493;margin-top:8px}
@media(max-width:980px){.top-grid{grid-template-columns:1fr}.canvas-wrap canvas{max-height:60vh}}
@media(max-width:600px){.app{padding:14px 10px 30px}.card{padding:13px}}
</style></head><body><main class="app">
<header class="head"><div><span class="badge">模拟账本联动 · 本地生成</span><h1>交易图片与战绩</h1><p>直接使用你上传的两份模板：卖出/推票卡自动填成交信息并绘制行情图；战绩表按已确认买卖记录汇总。</p></div>
<div class="row"><a class="button-link" href="/trading">返回交易中心</a><button id="refreshRecords" class="button-secondary" type="button">刷新交易记录</button></div></header>
<div class="notice"><strong>仅教学模拟：</strong>交易明细来自本工作台模拟账本，不代表真实证券成交。走势图使用 Yahoo Finance 历史日线，由 TradingView Lightweight Charts 绘制并自动截图；图表网络请求由本工作台读取。模板与 PNG 在当前电脑本地处理。</div>
<section class="top-grid">
<div class="stack">
<section class="card"><h2>1 · 选择模板与交易记录</h2>
<label class="field"><span>模板</span><select id="templateMode"><option value="performance">战绩表 · 每日收益汇总</option><option value="recommendation">推票/卖出卡 · 含自动走势图</option><option value="custom">上传自定义图片模板</option></select></label>
<label class="field"><span>模拟持仓 / 买卖记录</span><select id="holdingSelect"><option value="">正在读取交易记录…</option></select></label>
<label class="field"><span>卡片记录类型</span><select id="eventMode"><option value="sell">卖出记录</option><option value="buy">买入记录</option></select></label>
<label class="field"><span>卡片日期（模板中自动居中）</span><input id="saleDate" type="date"></label>
<div id="reasonGroup" class="field"><span>卖出理由（由你填写）</span><textarea id="sellReason" maxlength="500" placeholder="填写卖出原因；此处留空则图片中不显示示例理由"></textarea></div>
<label id="targetGroup" class="field"><span>目标价（仅手动填写；非账本成交价）</span><input id="targetPrice" maxlength="60" placeholder="可选"></label>
<label id="stopGroup" class="field"><span>止损价（仅手动填写）</span><input id="stopLoss" maxlength="60" placeholder="可选"></label>
<div id="chartOptions" class="row"><label class="field" style="flex:1;min-width:140px;margin:0"><span>走势图周期</span><select id="chartRange"><option value="6mo">6个月</option><option value="1y" selected>1年</option><option value="5y">5年</option></select></label><button id="refreshChart" class="button-secondary" type="button">刷新走势图</button></div>
<div id="customUpload" class="field hidden"><span>自定义模板图片</span><input id="templateFile" class="file-input" type="file" accept="image/png,image/jpeg,image/webp"></div>
<div class="row" style="margin-top:12px"><button id="exportPng" class="button" type="button" disabled>下载当前 PNG</button><button id="exportAll" class="button-secondary hidden" type="button">导出全部战绩页</button></div>
<div id="loadStatus" class="status" role="status">正在读取模拟账本…</div><div id="chartStatus" class="status" role="status" aria-live="polite"></div>
<div class="statsline"><span id="dataCount" class="stat-chip">战绩读取中</span><span id="dailyReturnNote" class="stat-chip">按卖出日期与币种分别计算；顶部为各日收益率相加/相减，不跨币种换算、非复利</span></div>
</section>
<section class="card"><h2>模板与数据说明</h2><p class="hint">内置模板按原 PPTX 版面坐标重建，表格与字段会居中落在预留区域。推票卡日期读取买入或卖出成交时间；战绩表最多每页显示 19 笔，超出可分页或一次导出全部分页。买入价、卖出价和日期仅来自人工确认的模拟交易。</p><p class="chart-source">走势图：Yahoo Finance 日线收盘价；白底、关闭网格线，带价格轴、日期轴及轻微阴影。行情暂不可用时，可重试；不会拿模板里的示例图冒充真实行情。</p></section>
</div>
<section class="card"><div class="section-head"><h2>2 · 模板预览</h2><div id="performancePager" class="pager hidden"><button id="prevPage" class="button-secondary" type="button">上一页</button><span id="pageLabel" class="hint"></span><button id="nextPage" class="button-secondary" type="button">下一页</button></div></div>
<div id="canvasWrap" class="canvas-wrap"><div id="canvasEmpty" class="canvas-empty">正在读取模板与模拟记录…</div><canvas id="preview" width="1600" height="900" hidden aria-label="交易图片模板与自动生成的模拟记录"></canvas></div>
<div id="editorStatus" class="status" role="status"></div></section>
</section>
<section id="customFieldsCard" class="card hidden" style="margin-top:14px"><h2>自定义模板字段与位置</h2><p class="subnote">仅自定义图片需要手动调整；内置两份 PPTX 模板使用已校准的预留位置。</p><div id="customFields"></div></section>
<section class="card" style="margin-top:14px"><div class="section-head"><h2>战绩统计预览</h2><span class="badge">数据源：65 人模拟账本</span></div><p class="subnote">每日按布加勒斯特卖出日期与币种分别汇总：该币种当日模拟净盈亏 ÷ 当日卖出仓位的买入成本；顶部将各币种每日百分比相加/相减，不含未实现盈亏、不做汇率换算，也不是复利或真实账户收益。</p><div id="dailyRows" class="status">读取中…</div></section>
</main><div id="chartHost" aria-hidden="true"></div>
<script src="/static/vendor/lightweight-charts-5.2.0.js" defer></script><script src="/static/app/image-editor.js" defer></script>
</body></html>'''
