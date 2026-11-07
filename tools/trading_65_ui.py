"""One self-contained simulated trading tab; keeps existing writing and themes unchanged."""

SECTION = r'''
<style>
.sim-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:17px 0}
.sim-record{background:#fff;border:1px solid #dce4ec;border-radius:14px;padding:18px;margin:18px 0}
.sim-record-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0}
.sim-record-grid label{display:flex;flex-direction:column;gap:5px;font-size:12px;font-weight:700;color:#344354}
.sim-record-grid input,.sim-record-grid select{min-height:40px;max-width:100%;width:100%;padding:8px;border:1px solid #d1d9e2;border-radius:8px;background:#fff}
.sim-record-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.sim-record-actions button{min-height:40px}
@media(max-width:900px){.sim-record-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:500px){.sim-record-grid{grid-template-columns:1fr}}

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

/* One-click recommendation: individual persona cards, never a flat anonymous row. */
.sim-recommend-host{overflow:visible;max-height:none;border:0;background:transparent;border-radius:0}
.sim-recommend-overview{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin:14px 0}
.sim-recommend-overview strong{font-size:14px;color:#26313e}
.sim-recommend-overview small{color:#6a7582}
.sim-candidate-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.sim-candidate-card{border:1px solid #e1e6ec;background:#fff;padding:19px;border-radius:15px;
 box-shadow:0 3px 12px #17233208;min-width:0;transition:border-color .22s ease,box-shadow .22s ease,transform .22s ease}
.sim-person-head{display:flex;align-items:center;gap:13px;min-width:0}
.sim-person-avatar{width:48px;height:48px;display:grid;place-items:center;flex-shrink:0;
 background:#f0f3f7;border:1px solid #e3e8f0;color:#344353;border-radius:14px;font-size:15px;font-weight:800}
.sim-person-identity{min-width:0;flex:1}.sim-person-identity h3{font-size:15px;font-weight:800;line-height:1.45;
 margin:0;color:#202c38;overflow-wrap:anywhere}.sim-person-identity small{display:block;font-size:11px;color:#747f8c}
.sim-person-status{font-size:11px;color:#465363;background:#f3f5f8;border-radius:99px;padding:5px 9px;
 border:1px solid #e5e9ef;white-space:nowrap}
.sim-person-detail{margin:13px 0 8px;color:#596574;font-size:12px;line-height:1.65;
 min-height:37px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.sim-person-tags{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 14px}
.sim-person-tags span{background:#f5f7f9;color:#535f6b;border:1px solid #e9edf1;padding:4px 8px;
 border-radius:7px;font-size:11px}
.sim-person-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;padding:13px;
 border:1px solid #ecf0f3;background:#fbfcfd;border-radius:10px}
.sim-person-facts small{display:block;font-size:11px;color:#798390}
.sim-person-facts b{font-size:12px;color:#2a3440;font-weight:750;overflow-wrap:anywhere}
.sim-person-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:14px}
.sim-person-actions button{padding:9px 13px;font-size:12px}
.sim-person-actions [data-qty]{width:96px;min-height:38px;max-width:100%;padding:7px 9px}
.sim-recommend-empty{border:1px dashed #cdd4dd;background:#fff;border-radius:12px;padding:21px;color:#596573}
@media(hover:hover) and (pointer:fine){.sim-candidate-card:hover{transform:translateY(-3px);
 border-color:#bdc8d4;box-shadow:0 14px 28px #17233217}}
@media(max-width:950px){.sim-candidate-grid{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.sim-candidate-card{transition:none}
 .sim-candidate-card:hover{transform:none}}
@media(max-width:900px){.sim-grid{grid-template-columns:1fr}.sim-counters{grid-template-columns:repeat(2,1fr)}}
/* Consistent readable type scale, borders and controls in the trading center. */
.sim-grid{gap:18px}
.sim-counters{gap:12px}
.sim-counter{border-color:#e4e8ed;border-radius:12px;min-width:0}
.sim-counter small{font-size:12px;line-height:1.5}
.sim-alert,.sim-label{font-size:13px;line-height:1.65}
.sim-table{font-size:13px}
.sim-table th,.sim-table td{padding:12px 13px;line-height:1.55}
.sim-table input{font-size:13px;min-height:40px;border-radius:9px}
.sim-table button{font-size:13px;min-height:40px;border-radius:9px}
.sim-candidate-card{border-color:#e4e8ed;border-radius:12px;padding:18px}
.sim-person-identity small,.sim-person-status{font-size:12px}
.sim-person-status{line-height:1.5}
.sim-person-detail,.sim-person-facts b{font-size:13px}
.sim-person-tags span,.sim-person-facts small{font-size:12px;line-height:1.5}
.sim-person-actions button{font-size:13px;min-height:40px}
.sim-person-actions [data-qty]{min-height:40px;font-size:13px}
.sim-tag{font-size:12px;line-height:1.5}
.sim-recommend-overview small{font-size:12px;line-height:1.5}
.sim-tablewrap{border-color:#e4e8ed;border-radius:12px}
@media(max-width:600px){
 .sim-person-head{flex-wrap:wrap}
 .sim-person-status{margin-left:auto}
 .sim-candidate-card{padding:15px}
 .sim-person-actions button{flex:1 1 auto}
 .sim-person-facts{grid-template-columns:1fr}
}
</style>
<div class="section" id="tab-sim">
<div class="sim-alert">仅限65名虚构成员的教学模拟账本；买入、卖出、持仓、资金及成交价格均为用户填写的模拟数据，不是证券市场真实执行结果。未配置模拟开户与资金的成员不能自动买入。</div>
<div class="sim-counters" id="sim-stats"><div class="sim-counter">加载中…</div></div>
<div class="status" id="sim-message">交易数据尚未载入。</div>
<section class="sim-record" id="participant-records" aria-labelledby="trade-record-title">
<h2 id="trade-record-title">参与人员交易记录与明细导出</h2>
<p class="muted">此处只负责人工登记参与人员的交易信息及导出已保存明细；不选股、不下单、不自动改动持仓。当前数据源为原65人v4.1模拟账本，录入事实未经证券账户核验。</p>
<div class="sim-record-grid">
 <label>参与人员<select id="trade-record-person"></select></label>
 <label>买卖方向<select id="trade-record-type"><option value="buy">买入</option><option value="sell">卖出</option></select></label>
 <label>交易日期<input id="trade-record-date" type="date" required></label>
 <label>股票代码<input id="trade-record-symbol" maxlength="30" placeholder="例如 TLV"></label>
 <label>股票名称<input id="trade-record-name" maxlength="120"></label>
 <label>市场<input id="trade-record-market" value="BVB" maxlength="40"></label>
 <label>股数<input id="trade-record-quantity" type="number" min="1" step="1"></label>
 <label>单价<input id="trade-record-price" type="number" min="0.000001" step="any"></label>
 <label>币种<select id="trade-record-currency"><option>RON</option><option>EUR</option><option>USD</option><option>GBP</option><option>HKD</option><option>CNY</option></select></label>
 <label>参考编号（选填）<input id="trade-record-reference" maxlength="120"></label>
 <label style="grid-column:span 2">备注（选填）<input id="trade-record-note" maxlength="500"></label>
</div>
<div class="sim-record-actions"><button type="button" id="trade-record-save">保存本条交易记录</button><span id="trade-record-feedback" role="status">未提交记录。</span></div>
<hr>
<h3>导出已保存交易明细（CSV，Excel可打开）</h3>
<div class="sim-record-grid">
 <label>人员筛选<select id="trade-export-person"><option value="">全部参与人员</option></select></label>
 <label>买卖筛选<select id="trade-export-type"><option value="">全部</option><option value="buy">买入</option><option value="sell">卖出</option></select></label>
 <label>起始日期<input id="trade-export-start" type="date"></label>
 <label>结束日期<input id="trade-export-end" type="date"></label>
</div>
<div class="sim-record-actions"><button type="button" id="trade-export-csv">导出已保存明细 CSV</button><small>没有符合条件的记录时仅导出表头；不填充演示成交。</small></div>
<h3 style="margin-top:18px">已保存参与人员交易明细</h3>
<div id="trade-record-list" class="sim-tablewrap" aria-live="polite"></div>
</section>
<details id="sim-legacy" class="sim-record"><summary style="cursor:pointer;font-weight:750">旧版模拟计划及买卖流程（保留已有数据，非当前主要职责）</summary>
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
<div class="row"><button id="sim-recommend">一键推荐交易人员</button><button class="alt" id="sim-refresh">刷新交易账本</button><button class="alt" id="sim-snapshot">查看当前交易事实快照</button></div>
<div id="sim-candidate-list" class="sim-recommend-host" aria-live="polite"></div>
<pre id="sim-snapshot-out" hidden></pre>
</section>
<div class="sim-grid">
<section class="card"><h2>04 · 持仓及卖出</h2><div class="sim-tablewrap" id="sim-holdings"></div></section>
<section class="card"><h2>05 · 买卖记录（仅人工确认后生成）</h2><div class="sim-tablewrap" id="sim-transactions"></div></section>
</div>
<section class="card"><h2>65人实际交易资格明细</h2><p class="muted">此处65名全量展示；不具备模拟开户/资金条件的成员仍保留人物资料，但不会冒充已成交。</p><input id="sim-people-search" type="search" placeholder="搜索人物编号、姓名、职业、城市"><div class="sim-tablewrap" id="sim-people-table" style="margin-top:12px"></div></section>
</details>
</div>
'''

SCRIPT = r'''<script>
(function(){
'use strict';
const tradeRoot=document.getElementById('tab-sim');
const byid=s=>document.getElementById(s);
async function api(path,payload){
 const options=payload===undefined
  ? {credentials:'same-origin'}
  : {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)};
 const response=await fetch(path,options);
 let data;
 try{data=await response.json()}
 catch(error){throw new Error('接口没有返回有效JSON（HTTP '+response.status+'）')}
 if(!response.ok)throw new Error(data?.error||'HTTP '+response.status);
 return data;
}
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
function updateRecordSelectors(){
 const a=byid('trade-record-person'),b=byid('trade-export-person');
 const selected=a.value,filtered=b.value;
 a.innerHTML=tradeData.people.map(p=>'<option value="'+p.id+'">'+escapeHtml(p.id+' · '+p.name)+'</option>').join('');
 b.innerHTML='<option value="">全部参与人员</option>'+a.innerHTML;
 a.value=tradeData.people.some(x=>x.id===selected)?selected:'01';b.value=filtered;
 if(!byid('trade-record-date').value)byid('trade-record-date').value=tradeData.market_date;
}
function renderRecordList(){
 const offers=new Map(tradeData.offers.map(x=>[x.id,x]));
 const holds=new Map(tradeData.holdings.map(x=>[x.id,x]));
 const entries=[...tradeData.transactions].reverse().map(t=>{
   const h=holds.get(t.holding_id)||{},o=offers.get(t.offer_id)||{};
   const day=t.trade_date||String(t.created_at||'').slice(0,10);
   return '<tr><td>'+escapeHtml(t.id)+'</td><td>'+escapeHtml((person(t.person_id)?.name||t.person_id)+' · '+t.person_id)+'</td>'
     +'<td>'+escapeHtml(t.type==='buy'?'买入':'卖出')+'</td>'
     +'<td>'+escapeHtml(t.symbol||h.symbol||o.symbol||'未标注')+'</td>'
     +'<td>'+escapeHtml(day)+'</td><td>'+escapeHtml(t.quantity)+'</td>'
     +'<td>'+escapeHtml(money(t.unit_price,t.currency))+'</td>'
     +'<td>'+escapeHtml(t.record_origin==='manual-entry'?'人工登记':'原模拟账本')+'</td>'
     +'<td>'+escapeHtml(t.note||'')+'</td></tr>';
 });
 byid('trade-record-list').innerHTML=entries.length
  ?rowTable(['记录ID','人员','买卖','代码','交易日期','数量','单价','来源','备注'],entries)
  :empty('尚未登记任何参与人员交易记录');
}
function render(){if(!tradeData)return;
const m=tradeData.metrics,curPerson=val('sim-member'),curOffer=val('sim-offer');
const tx=tradeData.transactions;
byid('sim-stats').innerHTML=[['已登记记录',tx.length],['手工录入',tx.filter(t=>t.record_origin==='manual-entry').length],['买入明细',tx.filter(t=>t.type==='buy').length],['卖出明细',tx.filter(t=>t.type==='sell').length]].map(x=>'<div class="sim-counter"><strong>'+x[1]+'</strong><small>'+x[0]+'</small></div>').join('');
byid('sim-member').innerHTML=tradeData.people.map(p=>'<option value="'+p.id+'">'+escapeHtml(p.id+' · '+p.name+' · '+p.role)+'</option>').join('');
byid('sim-member').value=person(curPerson)?curPerson:'01';infoPerson();
byid('sim-offer').innerHTML='<option value="">请选择股票计划</option>'+tradeData.offers.map(o=>'<option value="'+escapeHtml(o.id)+'">'+escapeHtml(o.symbol+' · '+o.name+' ('+o.currency+')')+'</option>').join('');
byid('sim-offer').value=tradeData.offers.some(o=>o.id===curOffer)?curOffer:(tradeData.offers.at(-1)?.id||'');
renderPeople();renderRecs();renderHoldings();renderTx();updateRecordSelectors();renderRecordList();
}
function currentRec(){return tradeData?.recommendations.find(r=>r.offer_id===val('sim-offer')&&r.date===val('sim-day'))}
function renderRecs(){
 const host=byid('sim-candidate-list'),r=currentRec();
 if(!r){host.innerHTML='<div class="sim-recommend-empty">选择股票计划，点击“一键推荐交易人员”。系统只从65人正式档案中挑选已明确设置模拟开户且资金满足条件的成员。</div>';return;}
 const offer=tradeData.offers.find(o=>o.id===r.offer_id);
 if(!offer){host.textContent='当前股票计划不存在';return;}
 const counts={pending:0,invited:0,rejected:0,bought:0};
 (r.candidates||[]).forEach(c=>{if(c.status in counts)counts[c.status]++});
 const note='<div class="sim-recommend-overview"><strong>推荐结果 · '+r.candidates.length+' / '+offer.participant_count+' 人</strong><small>待邀请 '+counts.pending+' · 已邀请 '+counts.invited+' · 已模拟买入 '+counts.bought+' · 已拒绝 '+counts.rejected+'</small></div>';
 if(!r.candidates.length){host.innerHTML=note+'<div class="sim-recommend-empty">没有符合模拟开户、资金与最低股数条件的成员。请先配置交易资格，不自动生成虚构成交。</div>';return;}
 const cards=r.candidates.map(c=>{
   const p=person(c.person_id);if(!p)return '';
   const status=c.status,display={pending:'待邀请',invited:'已邀请',rejected:'已拒绝',bought:'已模拟买入'}[status]||'待核实';
   const safeId=escapeHtml(p.id),traits=[...(Array.isArray(p.traits)?p.traits:[]),...(Array.isArray(p.investment_focus)?p.investment_focus.slice(0,2):[])].slice(0,5);
   const amount=p.funds?.[offer.currency],fundText=amount===undefined?'未配置':money(amount,offer.currency);
   const source=p.persona_description||'暂无人物定位补充';
   const action=(status==='pending'||status==='rejected'?'<button data-sim-action="invite" data-person="'+safeId+'">确认邀请</button> ':'')
    +(status==='pending'||status==='invited'?'<button class="alt" data-sim-action="reject" data-person="'+safeId+'">拒绝</button> ':'')
    +(status==='invited'?'<input data-qty="'+safeId+'" type="number" min="'+escapeHtml(offer.min_shares)+'" step="1" value="'+escapeHtml(offer.min_shares)+'" aria-label="'+safeId+'号模拟买入股数"><button data-sim-action="buy" data-person="'+safeId+'">确认模拟买入</button>':'')
    +(status==='bought'?'<span class="sim-tag good">已形成模拟持仓，可在持仓列表追踪</span>':'');
   return '<article class="sim-candidate-card" data-person-card="'+safeId+'">'
    +'<div class="sim-person-head"><div class="sim-person-avatar" aria-hidden="true">'+safeId+'</div>'
    +'<div class="sim-person-identity"><h3>'+safeId+' · '+escapeHtml(p.name)+'</h3><small>'+escapeHtml([p.gender,p.age?p.age+'岁':'年龄未录入',p.role].join(' · '))+'</small></div>'
    +'<span class="sim-person-status">'+escapeHtml(display)+'</span></div>'
    +'<div class="sim-person-detail">'+escapeHtml(source)+'</div>'
    +'<div class="sim-person-tags">'+traits.map(t=>'<span>'+escapeHtml(t)+'</span>').join('')+'</div>'
    +'<div class="sim-person-facts"><div><small>工作 / 城市</small><b>'+escapeHtml((p.occupation||'未知')+' · '+(p.city||'未知'))+'</b></div>'
    +'<div><small>参与频率 / 持仓笔数</small><b>'+escapeHtml(({HIGH:'高',MEDIUM:'中',LOW:'低'}[p.frequency]||'未配置')+' / '+p.hold_count+'笔')+'</b></div>'
    +'<div><small>模拟开户状态</small><b>'+(p.opened?'已模拟开户':'未配置')+'</b></div>'
    +'<div><small>该币种模拟资金上限</small><b>'+escapeHtml(fundText)+'</b></div>'
    +'<div><small>单票仓位偏好（人设）</small><b>'+escapeHtml(p.position_preference||'未注明')+'</b></div>'
    +'<div><small>计划最低购买</small><b>'+escapeHtml(offer.min_shares)+' 股 · '+escapeHtml(money(offer.min_shares*offer.unit_price,offer.currency))+'</b></div></div>'
    +'<div class="sim-person-actions">'+action+'</div></article>';
 }).join('');
 host.innerHTML=note+'<div class="sim-candidate-grid">'+cards+'</div>';
}
function renderHoldings(){const rows=[...tradeData.holdings].reverse().map(h=>{const p=person(h.person_id),end=new Date(h.planned_sell_at),ready=h.status==='holding'&&Date.now()>=end.getTime();return '<tr><td>'+escapeHtml((p?.name||h.person_id)+' · '+h.symbol)+'</td><td>'+escapeHtml(h.quantity+'股 · '+money(h.buy_price,h.currency))+'</td><td>'+escapeHtml(h.status==='sold'?'已模拟卖出':ready?'符合卖出条件':'持有中')+'</td><td>'+escapeHtml(end.toLocaleString('zh-CN'))+'</td><td>'+(ready?'<input data-sell-price="'+escapeHtml(h.id)+'" type="number" min="0.000001" step="any" placeholder="模拟卖价"> <button data-sim-action="sell" data-holding="'+escapeHtml(h.id)+'">确认卖出</button>':'—')+'</td></tr>'});byid('sim-holdings').innerHTML=rows.length?rowTable(['成员/股票','模拟买入','状态','最早卖出','操作'],rows):empty('暂无模拟持仓');}
function renderTx(){const rows=[...tradeData.transactions].reverse().map(t=>'<tr><td>'+escapeHtml(t.type==='buy'?'买入':'卖出')+'</td><td>'+escapeHtml((person(t.person_id)?.name)||t.person_id)+'</td><td>'+escapeHtml(t.quantity)+'</td><td>'+escapeHtml(money(t.unit_price,t.currency))+'</td><td>'+escapeHtml(new Date(t.created_at).toLocaleString('zh-CN'))+'</td></tr>');byid('sim-transactions').innerHTML=rows.length?rowTable(['类型','人物','股数','模拟价','记录时间'],rows):empty('尚无人工确认的买卖记录');}
async function load(){tradeData=await api('/api/trading/sim/state');if(!byid('sim-day').value)byid('sim-day').value=tradeData.market_date;render();setMsg('读取成功：65人数据源'+tradeData.source+'；模拟账本版本 '+tradeData.revision);}
async function act(action,payload){try{const r=await api('/api/trading/sim/action',{action,...payload});await load();setMsg('已保存：'+({'eligibility':'模拟交易设置','create_offer':'股票计划','recommend':'候选名单','invite':'邀请','reject':'拒绝','buy':'模拟买入','sell':'模拟卖出'}[action]||action)+'。账本版本 '+r.revision);}catch(e){setMsg('操作失败：'+e.message)}}
byid('trade-record-save').onclick=async()=>{
 const button=byid('trade-record-save'),info=byid('trade-record-feedback');
 const payload={
  person_id:val('trade-record-person'),trade_type:val('trade-record-type'),
  trade_date:val('trade-record-date'),symbol:val('trade-record-symbol'),
  name:val('trade-record-name'),market:val('trade-record-market'),
  quantity:val('trade-record-quantity'),unit_price:val('trade-record-price'),
  currency:val('trade-record-currency'),reference:val('trade-record-reference'),
  note:val('trade-record-note')
 };
 if(!confirm('确认保存这条人工填报记录？此操作不会提交真实证券订单。'))return;
 button.disabled=true;info.textContent='正在写入账本…';
 try{
  const r=await api('/api/trading/records/add',payload);
  await load();
  info.textContent='保存成功，记录编号：'+r.result.record.id+'；未经真实成交核验。';
 }catch(e){info.textContent='保存失败：'+e.message}
 finally{button.disabled=false}
};
byid('trade-export-csv').onclick=async()=>{
 const button=byid('trade-export-csv');
 const params=new URLSearchParams();
 for(const [field,id] of Object.entries({
  person_id:'trade-export-person',trade_type:'trade-export-type',
  start_date:'trade-export-start',end_date:'trade-export-end'
 })){if(val(id))params.set(field,val(id))}
 if(val('trade-export-start')&&val('trade-export-end')&&
    val('trade-export-start')>val('trade-export-end')){
  byid('trade-record-feedback').textContent='导出失败：开始日期晚于结束日期';return;
 }
 button.disabled=true;
 try{
  const r=await fetch('/api/trading/records/export.csv?'+params.toString(),
                     {credentials:'same-origin'});
  if(!r.ok){const j=await r.json();throw Error(j.error||'HTTP '+r.status)}
  const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='participant-trade-details.csv';document.body.append(a);a.click();a.remove();
  URL.revokeObjectURL(url);
  byid('trade-record-feedback').textContent='已从服务器读取导出文件；浏览器开始下载。';
 }catch(e){byid('trade-record-feedback').textContent='导出失败：'+e.message}
 finally{button.disabled=false}
};
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