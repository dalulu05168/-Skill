"""One self-contained simulated trading tab; keeps existing writing and themes unchanged."""

SECTION = r'''
<style>
.sim-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:17px 0}
.sim-counters{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}
.sim-counter{border:1px solid #e6e4e0;border-radius:13px;padding:14px;background:#fff}
.sim-counter strong{display:block;font-size:23px;color:#292d2f}
.sim-counter small{display:block;font-size:11px}
.sim-inline{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.sim-inline>*{flex:1;min-width:110px}
.sim-tablewrap{overflow:auto;max-height:460px;border:1px solid #e4e5e6;border-radius:12px}
.sim-table{width:100%;border-collapse:collapse;font-size:12px;white-space:nowrap}
.sim-table th,.sim-table td{padding:10px 12px;border-bottom:1px solid #ececee;text-align:left}
.sim-table th{position:sticky;top:0;background:#f5f6f6;color:#64696c}
.sim-table input{width:96px;padding:7px 8px;font-size:12px}
.sim-table button{padding:7px 9px;font-size:12px}
.sim-tag{padding:3px 7px;border-radius:20px;background:#f2f3f4;color:#586066}
.sim-tag.good{background:#eef7f2;color:#28694b}
.sim-tag.warn{background:#fcf2dd;color:#93652a}
.sim-alert{font-size:12px;color:#6a655b;background:#faf6ea;border:1px solid #eae3d4;padding:12px 14px;border-radius:12px}
.sim-label{font-size:12px;color:#596068;margin:2px 0}
#sim-message{min-height:20px}
@media(max-width:900px){.sim-grid{grid-template-columns:1fr}.sim-counters{grid-template-columns:repeat(2,1fr)}}
</style>
<div class="section" id="tab-sim">
<div class="sim-alert">仅限65名虚构成员的教学模拟账本；买入、卖出、持仓、资金及成交价格均为用户填写的模拟数据，不是证券市场真实执行结果。未配置模拟开户与资金的成员不能自动买入。</div>
<div class="sim-counters" id="sim-stats"><div class="sim-counter">加载中…</div></div>
<div class="status" id="sim-message">交易数据尚未载入。</div>
<div class="sim-grid">
 <section class="card"><h2>01 · 65人成员交易资料</h2><p class="muted">姓名、职业等来自同一份65人v4.1正式人物资料；模拟开户、资金与参与频率独立设置，不修改人物原档案。</p>
 <label for="sim-member">选择人物</label><select id="sim-member"></select>
 <div class="sim-inline"><div><label for="sim-opened">模拟开户</label><select id="sim-opened"><option value="0">未配置 / 未开户</option><option value="1">已模拟开户</option></select></div><div><label for="sim-frequency">参与频率</label><select id="sim-frequency"><option value="MEDIUM">中</option><option value="HIGH">高</option><option value="LOW">低</option></select></div></div>
 <div class="sim-inline"><div><label for="sim-currency">模拟资金币种</label><select id="sim-currency"><option>RON</option><option>EUR</option><option>USD</option><option>GBP</option><option>HKD</option><option>CNY</option></select></div><div><label for="sim-funds">模拟可用资金上限</label><input id="sim-funds" type="number" min="0" step="0.01" placeholder="留空则未配置"></div></div>
 <label for="sim-required">今天指定参与</label><select id="sim-required"><option value="0">否</option><option value="1">是</option></select>
 <div class="row"><button id="sim-save-member">保存本人成员交易设置</button></div>
 </section>
 <section class="card"><h2>02 · 建立股票模拟计划</h2><p class="muted">按旧规则设置股票、市场、币种、模拟单价、最低股数、持有天数和参与人数。没有自动填充假行情。</p>
 <div class="sim-inline"><div><label for="sim-symbol">股票代码</label><input id="sim-symbol" maxlength="30" placeholder="如 TLV"></div><div><label for="sim-stock-name">股票名称</label><input id="sim-stock-name" maxlength="120" placeholder="手动输入"></div></div>
 <div class="sim-inline"><div><label for="sim-market">市场</label><input id="sim-market" value="BVB" maxlength="40"></div><div><label for="sim-offer-currency">币种</label><select id="sim-offer-currency"><option>RON</option><option>EUR</option><option>USD</option><option>GBP</option><option>HKD</option><option>CNY</option></select></div></div>
 <div class="sim-inline"><div><label for="sim-price">模拟单价</label><input id="sim-price" type="number" min="0.000001" step="any" placeholder="必填"></div><div><label for="sim-min-shares">最低股数</label><input id="sim-min-shares" type="number" min="1" value="1"></div></div>
 <div class="sim-inline"><div><label for="sim-hold-days">最少持有天数</label><input id="sim-hold-days" type="number" min="0" value="3"></div><div><label for="sim-participants">参与人数（上限65）</label><input id="sim-participants" type="number" min="1" max="65" value="8"></div></div>
 <label for="sim-discount">计划折扣比例（仅说明字段，不改变手动单价）</label><input id="sim-discount" type="number" min="0" max="99" value="0">
 <div class="row"><button id="sim-create-offer">建立模拟股票计划</button></div>
 </section>
</div>
<section class="card" style="margin-top:16px"><h2>03 · 股票计划 / 推荐与邀请</h2>
<div class="sim-inline"><div><label for="sim-offer">股票计划</label><select id="sim-offer"><option value="">尚无计划</option></select></div><div><label for="sim-day">罗马尼亚市场日期</label><input type="date" id="sim-day"></div></div>
<div class="row"><button id="sim-recommend">按旧规则生成当日候选名单</button><button class="alt" id="sim-refresh">刷新交易账本</button><button class="alt" id="sim-snapshot">查看当前交易事实快照</button></div>
<div id="sim-candidate-list" class="sim-tablewrap" style="margin-top:16px"></div>
<pre id="sim-snapshot-out" hidden></pre>
</section>
<div class="sim-grid">
<section class="card"><h2>04 · 持仓及卖出</h2><div class="sim-tablewrap" id="sim-holdings"></div></section>
<section class="card"><h2>05 · 买卖记录（仅人工确认后生成）</h2><div class="sim-tablewrap" id="sim-transactions"></div></section>
</div>
<section class="card"><h2>65人实际交易资格明细</h2><p class="muted">此处65名全量展示；不具备模拟开户/资金条件的成员仍保留人物资料，但不会冒充已成交。</p><input id="sim-people-search" type="search" placeholder="搜索人物编号、姓名、职业、城市"><div class="sim-tablewrap" id="sim-people-table" style="margin-top:12px"></div></section>
</div>
'''

SCRIPT = r'''<script>
(function(){
'use strict';
const tradeRoot=document.getElementById('tab-sim');
const byid=s=>document.getElementById(s);
const escapeHtml=s=>String(s===null||s===undefined?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let tradeData=null,initialized=false;
function setMsg(s){byid('sim-message').textContent=s}
function val(id){return byid(id).value}
function person(id){return tradeData?.people?.find(p=>p.id===id)}
function money(n,c){return (c||'RON')+' '+Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2})}
function rowTable(headers,rows){return '<table class="sim-table"><thead><tr>'+headers.map(s=>'<th>'+escapeHtml(s)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>'}
function empty(s){return '<p class="muted" style="padding:12px">'+escapeHtml(s)+'</p>'}
function infoPerson(){const p=person(val('sim-member'));if(!p)return;
byid('sim-opened').value=p.opened?'1':'0';byid('sim-frequency').value=p.frequency||'MEDIUM';byid('sim-required').value=p.required_today?'1':'0';
byid('sim-funds').value=p.funds?.[val('sim-currency')]??'';
}
function renderPeople(){const q=val('sim-people-search').toLowerCase().trim();const rows=tradeData.people.filter(p=>[p.id,p.name,p.occupation,p.city].join(' ').toLowerCase().includes(q)).map(p=>'<tr><td>'+escapeHtml(p.id)+'</td><td>'+escapeHtml(p.name)+'</td><td>'+escapeHtml(p.role)+'</td><td>'+escapeHtml(p.occupation)+'</td><td>'+escapeHtml(p.city)+'</td><td><span class="sim-tag '+(p.opened?'good':'warn')+'">'+(p.opened?'模拟已开户':'未配置开户')+'</span></td><td>'+p.hold_count+'</td></tr>');
byid('sim-people-table').innerHTML=rows.length?rowTable(['编号','姓名','分类','职业','城市','模拟资格','持仓笔数'],rows):empty('没有匹配成员');}
function render(){if(!tradeData)return;
const m=tradeData.metrics,curPerson=val('sim-member'),curOffer=val('sim-offer');
byid('sim-stats').innerHTML=[['65人资料',m.people],['已配置模拟开户',m.opened],['当前持仓人数',m.holding_members],['已确认卖出记录',m.sold_records]].map(x=>'<div class="sim-counter"><strong>'+x[1]+'</strong><small>'+x[0]+'</small></div>').join('');
byid('sim-member').innerHTML=tradeData.people.map(p=>'<option value="'+p.id+'">'+escapeHtml(p.id+' · '+p.name+' · '+p.role)+'</option>').join('');
byid('sim-member').value=person(curPerson)?curPerson:'01';infoPerson();
byid('sim-offer').innerHTML='<option value="">请选择股票计划</option>'+tradeData.offers.map(o=>'<option value="'+escapeHtml(o.id)+'">'+escapeHtml(o.symbol+' · '+o.name+' ('+o.currency+')')+'</option>').join('');
byid('sim-offer').value=tradeData.offers.some(o=>o.id===curOffer)?curOffer:(tradeData.offers.at(-1)?.id||'');
renderPeople();renderRecs();renderHoldings();renderTx();
}
function currentRec(){return tradeData?.recommendations.find(r=>r.offer_id===val('sim-offer')&&r.date===val('sim-day'))}
function renderRecs(){const r=currentRec();if(!r){byid('sim-candidate-list').innerHTML=empty('选择计划并点击“生成当日候选名单”；若无开户资金资料，将不会虚构成员交易。');return;}
const offer=tradeData.offers.find(o=>o.id===r.offer_id);
const rows=r.candidates.map(c=>{const p=person(c.person_id);const status=c.status,display={pending:'待邀请',invited:'已邀请',rejected:'已拒绝',bought:'已买入'}[status]||status;return '<tr><td>'+escapeHtml(c.person_id+' · '+(p?.name||''))+'</td><td>'+escapeHtml(display)+'</td><td>'+escapeHtml(money(p?.funds?.[offer.currency],offer.currency))+'</td><td>'+((status==='pending'||status==='rejected')?'<button data-sim-action="invite" data-person="'+c.person_id+'">邀请</button> ':'')+((status==='pending'||status==='invited')?'<button class="alt" data-sim-action="reject" data-person="'+c.person_id+'">拒绝</button> ':'')+(status==='invited'?'<input data-qty="'+c.person_id+'" type="number" min="'+offer.min_shares+'" value="'+offer.min_shares+'" aria-label="买入股数"> <button data-sim-action="buy" data-person="'+c.person_id+'">确认模拟买入</button>':'')+'</td></tr>'});
byid('sim-candidate-list').innerHTML=r.candidates.length?rowTable(['成员','当前状态','模拟资金上限','交易操作'],rows):empty('没有符合已开户、模拟资金及最低购买条件的成员。请先设置人物交易资格。');
}
function renderHoldings(){const rows=[...tradeData.holdings].reverse().map(h=>{const p=person(h.person_id),end=new Date(h.planned_sell_at),ready=h.status==='holding'&&Date.now()>=end.getTime();return '<tr><td>'+escapeHtml((p?.name||h.person_id)+' · '+h.symbol)+'</td><td>'+escapeHtml(h.quantity+'股 · '+money(h.buy_price,h.currency))+'</td><td>'+escapeHtml(h.status==='sold'?'已模拟卖出':ready?'符合卖出条件':'持有中')+'</td><td>'+escapeHtml(end.toLocaleString('zh-CN'))+'</td><td>'+(ready?'<input data-sell-price="'+escapeHtml(h.id)+'" type="number" min="0.000001" step="any" placeholder="模拟卖价"> <button data-sim-action="sell" data-holding="'+escapeHtml(h.id)+'">确认卖出</button>':'—')+'</td></tr>'});byid('sim-holdings').innerHTML=rows.length?rowTable(['成员/股票','模拟买入','状态','最早卖出','操作'],rows):empty('暂无模拟持仓');}
function renderTx(){const rows=[...tradeData.transactions].reverse().map(t=>'<tr><td>'+escapeHtml(t.type==='buy'?'买入':'卖出')+'</td><td>'+escapeHtml((person(t.person_id)?.name)||t.person_id)+'</td><td>'+escapeHtml(t.quantity)+'</td><td>'+escapeHtml(money(t.unit_price,t.currency))+'</td><td>'+escapeHtml(new Date(t.created_at).toLocaleString('zh-CN'))+'</td></tr>');byid('sim-transactions').innerHTML=rows.length?rowTable(['类型','人物','股数','模拟价','记录时间'],rows):empty('尚无人工确认的买卖记录');}
async function load(){tradeData=await api('/api/trading/sim/state');if(!byid('sim-day').value)byid('sim-day').value=tradeData.market_date;render();setMsg('读取成功：65人数据源'+tradeData.source+'；模拟账本版本 '+tradeData.revision);}
async function act(action,payload){try{const r=await api('/api/trading/sim/action',{action,...payload});await load();setMsg('已保存：'+({'eligibility':'模拟交易设置','create_offer':'股票计划','recommend':'候选名单','invite':'邀请','reject':'拒绝','buy':'模拟买入','sell':'模拟卖出'}[action]||action)+'。账本版本 '+r.revision);}catch(e){setMsg('操作失败：'+e.message)}}
byid('sim-member').addEventListener('change',infoPerson);byid('sim-currency').addEventListener('change',infoPerson);byid('sim-people-search').addEventListener('input',()=>tradeData&&renderPeople());
byid('sim-offer').addEventListener('change',renderRecs);byid('sim-day').addEventListener('change',renderRecs);
byid('sim-save-member').onclick=()=>act('eligibility',{person_id:val('sim-member'),opened:val('sim-opened')==='1',frequency:val('sim-frequency'),required_today:val('sim-required')==='1',currency:val('sim-currency'),funds:val('sim-funds')});
byid('sim-create-offer').onclick=()=>act('create_offer',{symbol:val('sim-symbol'),name:val('sim-stock-name'),market:val('sim-market'),currency:val('sim-offer-currency'),unit_price:val('sim-price'),min_shares:val('sim-min-shares'),hold_days:val('sim-hold-days'),participant_count:val('sim-participants'),discount_pct:val('sim-discount')});
byid('sim-recommend').onclick=()=>act('recommend',{offer_id:val('sim-offer'),date:val('sim-day')});
byid('sim-refresh').onclick=()=>load().catch(e=>setMsg('刷新失败：'+e.message));
byid('sim-snapshot').onclick=async()=>{try{const r=await api('/api/trading/sim/snapshot?date='+encodeURIComponent(val('sim-day'))+'&offer_id='+encodeURIComponent(val('sim-offer')));byid('sim-snapshot-out').hidden=false;byid('sim-snapshot-out').textContent=JSON.stringify(r,null,2);}catch(e){setMsg(e.message)}};
tradeRoot.addEventListener('click',e=>{const b=e.target.closest('button[data-sim-action]');if(!b)return;const a=b.dataset.simAction,offer_id=val('sim-offer'),date=val('sim-day'),person_id=b.dataset.person;
if(a==='invite'||a==='reject')act(a,{offer_id,date,person_id});
if(a==='buy'){const quantity=tradeRoot.querySelector('[data-qty="'+person_id+'"]')?.value;if(!confirm('确认保存这笔教学模拟买入记录？'))return;act('buy',{offer_id,date,person_id,quantity});}
if(a==='sell'){const holding_id=b.dataset.holding,sell_price=[...tradeRoot.querySelectorAll('[data-sell-price]')].find(x=>x.dataset.sellPrice===holding_id)?.value;if(!confirm('确认保存这笔教学模拟卖出记录？'))return;act('sell',{holding_id,sell_price});}});
document.querySelector('[data-tab="sim"]').addEventListener('click',()=>{if(!initialized){initialized=true;load().catch(e=>{initialized=false;setMsg('加载失败：'+e.message)})}});
})();
</script>'''


def with_trading_ui(page):
    assert 'data-tab="script"' in page and '</body></html>' in page
    return (page.replace('<button class="active" data-tab="script">',
                         '<button data-tab="sim">模拟买卖与持仓</button><button class="active" data-tab="script">', 1)
                .replace('<div class="section active" id="tab-script">',
                         SECTION + '<div class="section active" id="tab-script">', 1)
                .replace('</body></html>', SCRIPT + '</body></html>', 1))