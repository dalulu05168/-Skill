'use strict';
const $ = id => document.getElementById(id);
let busy = false;
let current = null;
let hasFetched = false; // Data belongs only to the currently selected market, provider and theme.
const valid = q => ['OK', 'CLOSED'].includes(q.status) && Number.isFinite(q.last);
function setStatus(message, error=false) {
  $('status').textContent = message;
  $('status').className = error ? 'status error' : 'status';
}
function renderRows(rows) {
  $('rows').replaceChildren();
  for (const q of rows) {
    const tr = document.createElement('tr');
    const number = valid(q) ? q.last.toLocaleString('en-US',{maximumFractionDigits:4}) : '—';
    const rounded = valid(q) && Number.isFinite(q.pct) ? Number(q.pct.toFixed(2)) : null;
    const pct = rounded===null ? '' : (rounded>0?'+':'') + rounded.toFixed(2) + '%';
    const fields = [
      [q.label, q.symbol],
      [number, pct],
      [q.timestamp ? new Date(q.timestamp).toLocaleString() : '无有效时间',
       (q.source || '未知来源') + ' · ' + (q.status || 'NA') + ' · ' + (q.reason || '')]
    ];
    fields.forEach(([label, sub], fieldIndex) => {
      const td = document.createElement('td');
      td.textContent = label;
      const small = document.createElement('small');
      small.textContent = sub;
      if (fieldIndex === 1 && rounded !== null) {
        small.style.color = rounded>0 ? '#11964E' : rounded<0 ? '#C52A39' : '#576374';
        small.style.fontWeight = '400';
      }
      td.append(small);
      tr.append(td);
    });
    $('rows').append(tr);
  }
}
async function call(action) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('header button,header select').forEach(el => el.disabled = true);
  $('send').disabled = true;
  if (action === 'preview') { hasFetched = false; current = null; }
  setStatus(action === 'refresh' ? '正在获取并校验真实行情…' : action === 'preview' ? '正在显示所选空白模板…' : '正在处理…');
  try {
    const payload = {action, market:$('market').value, provider:$('provider').value,theme:$('theme').value};
    const response = await fetch('/api/tools', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok || data.error) throw Error(data.error || '处理失败');
    current = action === 'preview' ? null : data;
    if (action === 'refresh') hasFetched = true;
    $('preview').src = 'data:image/png;base64,' + data.image;
    $('caption').textContent = data.caption;
    renderRows(action === 'preview' ? [] : data.rows);
    if (action === 'preview') {
      $('caption').textContent = '';
      setStatus('已选择模板；点击「获取数据」后才填入数值和走势图');
      $('send').disabled = true;
      tvCardsEnabled = false;
      $('tvChart').textContent = '查看 TV 图表（不参与导出）';
      $('tvChart').setAttribute('aria-pressed','false');
      tvOverlay.replaceChildren();
      return;
    }
    // The PNG is the primary template. Never cover it automatically with an iframe:
    // the TV widget is separately viewable and cannot be captured in 4K export.
    if (action === 'refresh') {
      tvCardsEnabled = false;
      $('tvChart').textContent = '查看 TV 图表（不参与导出）';
      $('tvChart').setAttribute('aria-pressed','false');
      tvOverlay.replaceChildren();
    }
    const closed = data.rows.some(q => q.status === 'CLOSED');
    const invalid = data.rows.filter(q => q.status !== 'OK' || !valid(q)).map(q => q.label);
    const indexCount = data.rows.slice(0,3).filter(q=>q.chart_ready === true).length;
    const chartsNotice = '；当前模板已获得 '+indexCount+'/3 组原始分时序列';
    setStatus(data.sent ? 'Telegram 已返回发送成功' : data.publishable ?
      '行情报价已通过本次校验'+chartsNotice+'；请人工复核后发送' :
      closed ? '市场处于非开盘时段；当前仅可预览，不可按开盘行情发送'+chartsNotice :
      '尚未通过全部指标核验：' + invalid.join('、') + chartsNotice + '。数据缺失时图表留空，不允许发送');
    $('send').disabled = !data.publishable;
    if (data.file) {
      const link = document.createElement('a');
      link.href = 'data:' + data.mime + ';base64,' + data.file;
      link.download = data.name;
      link.click();
    }
  } catch (error) {
    setStatus(error.message, true);
    current = null;
    if (action === 'refresh') hasFetched = false;
    $('send').disabled = true;
    tvCardsEnabled = false;
    tvOverlay.replaceChildren();
  } finally {
    busy = false;
    document.querySelectorAll('header button,header select').forEach(el => el.disabled = false);
    $('export').disabled = !hasFetched;
    $('tvChart').disabled = !hasFetched;
    $('send').disabled = !hasFetched || !current?.publishable;
  }
}
$('market').onchange = () => call('preview');
$('theme').onchange = () => call('preview');
$('provider').onchange = () => call('preview');
$('refresh').onclick = () => call('refresh');
$('export').onclick = () => { if (hasFetched) call('export'); }; 
$('copy').onclick = async () => {
  try { await navigator.clipboard.writeText(current?.caption || '');setStatus('播报文案已复制'); }
  catch (error) { setStatus('复制失败：' + error.message, true); }
};
$('send').onclick = () => $('confirmSend').showModal();
$('cancelSend').onclick = () => $('confirmSend').close();
$('doSend').onclick = () => {$('confirmSend').close();call('send');};
call('preview');

// Hosted TradingView charts are displayed INSIDE the three approved index cards.
// These iframes are NOT the data used by the 4K PNG renderer. The exporter uses
// separately validated, provider-attributed intraday observations (BVB/Yahoo).
const TV_PALETTE={
 flow:{background:'#031530',grid:'rgba(118,180,222,0.12)'},
 glass:{background:'#142d40',grid:'rgba(203,232,247,0.12)'},
 graphite:{background:'#11171f',grid:'rgba(188,196,202,0.10)'},
 default:{background:'#050c17',grid:'rgba(160,180,205,0.10)'}
};
const TV_INDICES={
  RO:[['BET','BVB:BET'],['BET-NG','BVB:BETNG'],['BET-FI','BVB:BETFI']],
  US:[['DOW JONES','DJ:DJI'],['S&P 500','SP:SPX'],['NASDAQ','NASDAQ:IXIC']]
};
let tvCardsEnabled=false;
let tvChartsRequest=0;
const tvOverlay=$('tvInlineCharts');
function positionTvCards(){
 const img=$('preview');
 if(!tvCardsEnabled||!img.complete||!img.naturalWidth){tvOverlay.replaceChildren();return;}
 const stage=$('marketPreview').getBoundingClientRect();
 const rect=img.getBoundingClientRect();
 const mode=$('theme').value;
 tvOverlay.className='theme-'+mode;
 // Approved Canva 3840x2160 index-card chart rectangles, in 1920x1080 preview units.
 // The same geometry applies to FLOW / GLASS / GRAPHITE; DEFAULT remains legacy.
 const nativeBoxes=[0,1,2].map(i=>mode==='default'?
   [87+i*608,444,635+i*608,756]:
   [101+i*607,496,605+i*607,751]);
 for(const [i,card] of [...tvOverlay.children].entries()){
   const [x0,y0,x1,y1]=nativeBoxes[i];
   Object.assign(card.style,{
     left:(rect.left-stage.left+x0*rect.width/1920)+'px',
     top:(rect.top-stage.top+y0*rect.height/1080)+'px',
     width:((x1-x0)*rect.width/1920)+'px',
     height:((y1-y0)*rect.height/1080)+'px'
   });
 }
}
function mountTvCards(){
 tvOverlay.replaceChildren();
 if(!tvCardsEnabled || !hasFetched)return;
 const id=++tvChartsRequest;
 const market=$('market').value;
 const symbols=TV_INDICES[market]||[];
 for(const [label,symbol] of symbols){
   const card=document.createElement('div');card.className='tv-card';
   card.setAttribute('aria-label',label+' TradingView 图表');
   const widget=document.createElement('div');widget.className='tradingview-widget-container';
   const inner=document.createElement('div');inner.className='tradingview-widget-container__widget';
   widget.appendChild(inner);
   const credit=document.createElement('div');credit.className='tv-widget-credit';
   credit.textContent='TradingView · 以图表显示的时区/延迟为准';
   const fallback=document.createElement('div');fallback.className='tv-card-loading';
   fallback.textContent='连接 TradingView…';
   card.append(widget,credit,fallback);tvOverlay.appendChild(card);
   const script=document.createElement('script');script.async=true;
   script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
   script.textContent=JSON.stringify({
     autosize:true,symbol,interval:'1',
     timezone:market==='RO'?'Europe/Bucharest':'America/New_York',
     theme:'dark',style:'2',locale:'en',hide_top_toolbar:true,
     hide_side_toolbar:true,hide_legend:true,allow_symbol_change:false,
     save_image:true,withdateranges:false,
     backgroundColor:TV_PALETTE[$('theme').value].background,
     gridColor:TV_PALETTE[$('theme').value].grid
   });
   script.onerror=()=>{fallback.textContent='TV 图表不可用 · 未获取真实走势';};
   inner.appendChild(script);
   const observer=new MutationObserver(()=>{
     const iframe=inner.querySelector('iframe');
     if(iframe){iframe.addEventListener('load',()=>{fallback.style.display='none';},{once:true});observer.disconnect();}
   });
   observer.observe(inner,{childList:true,subtree:true});
   // We never infer that an iframe has loaded real exchange data from mere DOM creation.
   // The chart provider is responsible for the displayed delay and entitlement status.
 }
 positionTvCards();
}
$('tvChart').addEventListener('click',()=>{
  if (!hasFetched) return;
  tvCardsEnabled=!tvCardsEnabled;
  $('tvChart').textContent=tvCardsEnabled?'返回导出预览':'查看 TV 图表（不参与导出）';
  $('tvChart').setAttribute('aria-pressed',String(tvCardsEnabled));
  mountTvCards();
});
$('market').addEventListener('change',()=>{tvCardsEnabled=false; tvOverlay.replaceChildren();});
$('theme').addEventListener('change',()=>{tvCardsEnabled=false; tvOverlay.replaceChildren();});
$('preview').addEventListener('load',positionTvCards);
window.addEventListener('resize',positionTvCards);
if(typeof ResizeObserver!=='undefined')new ResizeObserver(positionTvCards).observe($('marketPreview'));