'use strict';
(() => {
const TZ='Europe/Bucharest', SLOTS=window.MATERIALS, FIELDS=window.FIELD;
const $ = id => document.getElementById(id);
const VERSION="5.0.0";
const KEYS={drafts:'bvb_pro2_drafts',news:'bvb_pro2_news',first:'bvb_pro2_baseline',seen:'bvb_pro2_seen',machineTranslation:'bvb_v33_translate_enabled'};
const store={get(k,def){try{const s=localStorage.getItem(k);return s?JSON.parse(s):def}catch{return def}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){console.error('本地存储失败',e);if(document.getElementById('toast'))showToast('本地存储失败，请立即导出资料包；本次内容可能未保存');}}};
let drafts=store.get(KEYS.drafts,{}),articles=store.get(KEYS.news,[]),sources=[],quote=null,connected=false,refreshing=false,baseline=store.get(KEYS.first,false),seen=new Set(store.get(KEYS.seen,[])),auto=true,nodeView='today',activeId='',lastDate='',newsSearch='',newsFilter='all',notifications=false,lastFetch='',tickNumber=0,toastTimer=0,lastClockTs=null,notifiedEvents=new Set(),activeReviewId=null,onlyFresh=false,translationEnabled=store.get(KEYS.machineTranslation,false),translating=false,translationFailures=0;
const fmt=(tz,opt)=>new Intl.DateTimeFormat('zh-CN',{timeZone:tz,...opt});
const partFmt=new Intl.DateTimeFormat('en-GB',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const getRO=(d=new Date())=>{const p=Object.fromEntries(partFmt.formatToParts(d).filter(x=>x.type!=='literal').map(x=>[x.type,+x.value]));return {...p,date:`${p.year}-${String(p.month).padStart(2,'0')}-${String(p.day).padStart(2,'0')}`,day:new Date(Date.UTC(p.year,p.month-1,p.day)).getUTCDay()}};
const groupOf=day=>day===6?'sat':day===0?'sun':'weekday';
const todaySlots=day=>SLOTS.filter(x=>x.day===groupOf(day));
const minOf=t=>Number(t.slice(0,2))*60+Number(t.slice(3,5));
const pad=n=>String(n).padStart(2,'0');
const escapeHtml=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const dateLabel=(ro=getRO())=>`${ro.year}年${ro.month}月${ro.day}日 星期${['日','一','二','三','四','五','六'][ro.day]}`;
const activeKey=()=>`${lastDate}/${activeId}`;
function getDraft(){if(!drafts[activeKey()])drafts[activeKey()]={fields:{},selected:[],approved:false,published:false,verifiedAt:null,approvedAt:null};return drafts[activeKey()]}
function saveDraft(){store.set(KEYS.drafts,drafts)}
function invalidate(d){d.approved=false;d.approvedAt=null;d.published=false;if($('reviewBox'))$('reviewBox').checked=false;saveDraft()}
function showToast(s){$('toast').textContent=s;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3500)}
function zonedTs(y,m,d,time){let [hh,mm]=time.split(':').map(Number),guess=Date.UTC(y,m-1,d,hh,mm);for(let i=0;i<3;i++){let p=getRO(new Date(guess));let actual=Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute);guess+=Date.UTC(y,m-1,d,hh,mm)-actual}return guess}
function upcomingEvent(now=new Date()) {const ro=getRO(now),nowTs=now.getTime(),events=[];for(let add=0;add<8;add++){const utc=new Date(Date.UTC(ro.year,ro.month-1,ro.day+add));const y=utc.getUTCFullYear(),m=utc.getUTCMonth()+1,d=utc.getUTCDate();todaySlots(utc.getUTCDay()).forEach(s=>{events.push({at:zonedTs(y,m,d,s.prep),type:'备料',slot:s,date:`${y}-${pad(m)}-${pad(d)}`});events.push({at:zonedTs(y,m,d,s.pub),type:'内容节点',slot:s,date:`${y}-${pad(m)}-${pad(d)}`})})}return events.filter(e=>e.at>nowTs).sort((a,b)=>a.at-b.at)[0]}
function clock(){const now=new Date(),ro=getRO(now),key=ro.date,minute=ro.hour*60+ro.minute;
 if(lastClockTs!==null&&notifications){const evt=upcomingEvent(new Date(lastClockTs));if(evt&&evt.at<=now.getTime()&&!notifiedEvents.has(`${evt.date}/${evt.slot.id}/${evt.type}`)){notifiedEvents.add(`${evt.date}/${evt.slot.id}/${evt.type}`);timedAlert(evt)}}lastClockTs=now.getTime();
 $('roTime').textContent=`${pad(ro.hour)}:${pad(ro.minute)}:${pad(ro.second)}`;
 $('roDate').textContent=`${dateLabel(ro)} · EEST/EET自动切换`;
 $('localTime').textContent=fmt('Asia/Kuala_Lumpur',{hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(now);
 $('localDate').textContent=fmt('Asia/Kuala_Lumpur',{year:'numeric',month:'2-digit',day:'2-digit',timeZoneName:'short'}).format(now);
 let next=upcomingEvent(now);if(next){let delta=Math.max(0,Math.floor((next.at-now.getTime())/1000));$('nextSlot').textContent=next.slot.title;$('nextAt').textContent=`${next.date} ${next.type} ${next.type==='备料'?next.slot.prep:next.slot.pub}`;$('nextCountdown').textContent=`${pad(Math.floor(delta/3600))}:${pad(Math.floor(delta%3600/60))}:${pad(delta%60)}`}
 const eligible=todaySlots(ro.day),slot=eligible.filter(s=>minOf(s.prep)<=minute).at(-1)||eligible[0];
 runCollectionClock(now);
 if(!slot){$('nextSlot').textContent='休市日：可手动整理资料';}
 if(ro.date!==lastDate){lastDate=key;renderTimeline();if(auto||!activeId)selectSlot((slot||SLOTS[0]).id,false)}
 else if(auto&&slot&&slot.id!==activeId){selectSlot((slot||SLOTS[0]).id,false)}
 else if(tickNumber++%30===0){renderTimeline();updatePreview()}
}
function selectSlot(id,manual=true){const x=SLOTS.find(s=>s.id===id);if(!x)return;activeId=id;if(manual){auto=false;$('autoNode').checked=false}renderTimeline();renderEditor()}
function renderTimeline(){const ro=getRO(),minute=ro.hour*60+ro.minute,items=nodeView==='all'?SLOTS:todaySlots(ro.day);$('nodeCount').textContent=items.length;
 $('timeline').innerHTML=items.map(s=>{let period=s.day===groupOf(ro.day)?(minute>=minOf(s.pub)?'今日已到内容节点':minute>=minOf(s.prep)?'正在备料':'待开始'):{weekday:'工作日',sat:'周六',sun:'周日'}[s.day];const draft=drafts[`${ro.date}/${s.id}`];return `<button class="slot ${activeId===s.id?'selected':''}" data-id="${s.id}"><time>${s.pub}<small>${s.prep}备料</small></time><span><span class="tt">${escapeHtml(s.title)}</span><span class="nd">${escapeHtml(s.tag)} · ${s.day==='weekday'?'工作日':s.day==='sat'?'周六':'周日'}</span><span class="state ${period==='正在备料'?'live':''}">${draft?.published?'已标记发布':draft?.approved?'审核通过':period}</span></span></button>`}).join('');
 $('timeline').querySelectorAll('.slot').forEach(b=>b.onclick=()=>selectSlot(b.dataset.id))}
function renderEditor(){const slot=SLOTS.find(s=>s.id===activeId);if(!slot)return;const ro=getRO(),draft=getDraft();$('slotTag').textContent=`${slot.tag.toUpperCase()} · ${slot.day==='weekday'?'工作日':slot.day==='sat'?'周六':'周日'}`;$('slotTitle').textContent=slot.title;$('slotInfo').textContent=`备料 ${slot.prep} · 内容节点 ${slot.pub}（罗马尼亚时间）｜${slot.focus}`;
 $('slotChecks').innerHTML=slot.checks.map(c=>`<div class="check-row">${escapeHtml(c)}</div>`).join('');
 $('fields').innerHTML=slot.fields.map(k=>`<div class="field"><label for="fld_${k}">${escapeHtml(FIELDS[k])}</label><textarea id="fld_${k}" data-field="${k}" placeholder="请填真实信息及时间 / 来源">${escapeHtml(draft.fields[k]||'')}</textarea></div>`).join('');
 $('fields').querySelectorAll('textarea').forEach(el=>el.addEventListener('input',()=>{draft.fields[el.dataset.field]=el.value;if(['bet','change'].includes(el.dataset.field))draft.quoteSource=null;invalidate(draft);updatePreview()}));
 $('reviewBox').checked=!!draft.approved;collectionUI();updatePreview()}
function cleanField(v){return String(v??'').trim()}
function unresolved(){const slot=SLOTS.find(s=>s.id===activeId),draft=getDraft();return slot.fields.filter(k=>!cleanField(draft.fields[k]))}
function buildLegacyText(includeStatus=true){const slot=SLOTS.find(s=>s.id===activeId),ro=getRO(),draft=getDraft();const vals={date:dateLabel(ro),time:`${pad(ro.hour)}:${pad(ro.minute)}（欧洲/布加勒斯特）`};for(const [k,v] of Object.entries(FIELDS))vals[k]=cleanField(draft.fields[k])||`【待核实：${v}】`;
 let result=slot.script.replace(/{{([a-z]+)}}/g,(m,k)=>vals[k]||m);
 const chosen=(draft.selected||[]).map(id=>articles.find(x=>x.id===id)).filter(a=>a?.verified);
 if(chosen.length){result+='\n\n—— 已记录人工核验的新闻来源（标题仅为摘要）——\n';for(let i=0;i<chosen.length;i++){let a=chosen[i];result+=`${i+1}. ${a.zhTitle?a.zhTitle+'（自动中文机翻，仅供审稿）\n原文：':''}${a.title}\n数据状态：${a.fetchStatus==='current'?'本次采集':'历史缓存，尚未重采'}\n来源：${a.source}${a.sources?.length>1?`（另有${a.sources.length-1}个关联来源）`:''}\n发布：${a.date?formatRODate(a.date):'未知（需核查）'}\n原文：${a.url}\n`}}
 result+=`\n—————————————————————————\n生成于：${dateLabel(ro)} ${pad(ro.hour)}:${pad(ro.minute)}:${pad(ro.second)}（罗马尼亚时间）\n说明：BVB资讯资料助手。此报告需核验行情及来源；新闻标题不能直接代表事实已确认。`;
 const miss=unresolved();if(includeStatus){result=`【${draft.approved?'已人工审核｜请注意行情时效':'草稿｜尚未完成全部核验，不宜直接发布'}】\n资料包：${slot.title} | 计划备料：${slot.prep} | 计划发布：${slot.pub}（罗马尼亚时间）\n—————————————————————————\n`+result;if(miss.length)result+=`\n\n未完成字段：${miss.map(k=>FIELDS[k]).join('、')}`;}return result}
function reviewErrors(){
 if(!activeId)return ['未选择资料节点'];
 const draft=getDraft(),slot=SLOTS.find(s=>s.id===activeId),missing=unresolved(),errs=[];
 if(missing.length)errs.push(`缺少 ${missing.length} 项必填资料：${missing.map(k=>FIELDS[k]).join('、')}`);
 for(const [k,value] of Object.entries(draft.fields||{}))if(/【待核实|【待填|模拟行情|示例数字/.test(String(value)))errs.push(`${FIELDS[k]||k}含未核实占位或示例`);
 const urls=(String(draft.fields.source||'').match(/https?:\/\/[^\s，、）]+/g)||[]).filter(x=>canonicalURL(x));
 if(!urls.length)errs.push('来源字段至少填写一个可访问的原始网页URL（请人工核对其内容）');
 for(const id of draft.selected||[]){const a=articles.find(x=>x.id===id);
  if(!a||!a.verified||!a.verifiedAt||!(a.reviewNote||'').trim()||a.reviewChecks?.some(x=>!x))errs.push(`已选新闻 ${a?.title||id} 缺少完整审核记录`);
  if(a&&a.fetchStatus!=='current')errs.push(`已选新闻 ${a.title} 目前只有历史缓存，不能作为本次资讯直接发布`)}
 const hasQuote=!!draft.quoteSource;
 if(hasQuote){const asof=dateMs(draft.quoteSource.marketTime);
  if(!Number.isFinite(asof))errs.push('引用BET行情未带可解析的观测时刻');
  else if(asof>Date.now()+120000||Date.now()-asof>90*60000)errs.push('引用BET行情距离当前超过90分钟或时间在未来；请更新报价或改填已标明交易日期的历史行情');
 }
 return errs;
}
function updatePreview(){
 if(!activeId)return;const draft=getDraft(),slot=SLOTS.find(s=>s.id===activeId),miss=unresolved(),errs=reviewErrors();
 if(draft.approved&&errs.length){draft.approved=false;draft.approvedAt=null;draft.published=false;saveDraft();}
 $('draft').textContent=buildText();$('fieldsProgress').textContent=`${slot.fields.length-miss.length} / ${slot.fields.length}`;
 $('draftFlag').textContent=draft.published?'已标记发布':draft.approved?'人工审核完成':'待核验';$('draftFlag').classList.toggle('ready',!!draft.approved);
 $('draftHint').textContent=draft.approved?'已记录人工审核 · 发布时仍需复核行情':`审核发现 ${errs.length} 类待办`;
 $('approvalHint').textContent=errs.length?`无法审核：${errs.length}类问题待解决`:'格式和选中资讯记录齐全；勾选后仍需人工承担原文核验责任';
 $('reviewFindings').classList.toggle('ok',errs.length===0);
 $('reviewFindings').textContent=errs.length?`发布检查：${errs.slice(0,4).join('；')}${errs.length>4?'；以及其他项':''}`:'字段、链接及人工新闻审核记录完整；系统无法自动保证实际数值正确。';
 $('markPublished').disabled=!draft.approved||errs.length>0;
}
const dateMs=s=>{const n=Date.parse(s);return Number.isFinite(n)?n:NaN};
const formatRODate=iso=>{const n=dateMs(iso);return Number.isFinite(n)?fmt(TZ,{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(n)):'未知'};
const normalized=s=>String(s).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const tokens=s=>new Set(normalized(s).split(/\s+/).filter(x=>x.length>=3));
function nearTitle(a,b){
 const x=normalized(a),y=normalized(b);if(!x||!y)return false;if(x===y)return true;
 const aa=tokens(a),bb=tokens(b);if(Math.min(aa.size,bb.size)<5)return false;
 const overlap=[...aa].filter(t=>bb.has(t)).length;
 return overlap/(aa.size+bb.size-overlap)>=.85;
}
function canonicalURL(raw){try{const u=new URL(raw);if(!/^https?:$/.test(u.protocol))return '';u.hash='';['utm_source','utm_medium','utm_campaign','utm_term','utm_content','fbclid','gclid'].forEach(p=>u.searchParams.delete(p));return u.toString().replace(/\/$/,'')}catch{return ''}}
const tickerPattern=/(?:\bTLV\b|\bBRD\b|\bH2O\b|\bSNP\b|\bSNG\b|\bSNN\b|\bEL\b|\bDIGI\b|\bBET(?:-NG)?\b)/i;
function getSymbols(text){const out=String(text).toUpperCase().match(/\b(?:TLV|BRD|H2O|SNP|SNG|SNN|EL|DIGI|BET-NG|BET)\b/g)||[];return [...new Set(out)].sort()}
function getEntity(text){const t=normalized(text);const s=getSymbols(text);if(s.length)return s.join(',');if(/banca transilvania/.test(t))return 'TLV';if(/hidroelectrica/.test(t))return 'H2O';if(/romgaz/.test(t))return 'SNG';if(/nuclearelectrica/.test(t))return 'SNN';if(/banca nationala|bnr\b/.test(t))return 'BNR';if(/european central bank|banca centrala europeana|banque centrale europeenne|\becb\b|\bbce\b/.test(t))return 'ECB';return ''}
function getEventType(text){const t=normalized(text);
 if(/(?:speech|discurs|interview|interviu|remarks|conferinta de presa)/.test(t))return '讲话/评论';
 if(/(?:suspend|suspendare|insolven|faliment|bankrupt|sanction|fraud)/.test(t))return '交易/监管风险';
 if(/(?:rate decision|interest rate decision|decizie de politica monetara|key rate|rata dobanzii de politica|dobanda cheie)/.test(t))return '利率决议';
 if(/(?:financial result|rezultat financiar|profit net|dividend|earnings|raport trimestrial)/.test(t))return '财报/分红';
 if(/(?:listing|listare|ipo|oferta publica|capital increase|majorare de capital|buyback)/.test(t))return '发行/资本事项';
 if(/(?:energy|energie|petrol|oil|gas price|gaz natural)/.test(t))return '能源';
 if(/(?:inflation|inflatie|gdp|pib|unemployment|somaj)/.test(t))return '经济数据';return '其他'}
function getNumbers(text){return [...new Set((String(text).match(/\b\d+(?:[.,]\d+)?\s*(?:%|bp|bps|miliarde|milioane|million|billion|lei|ron|eur|usd)\b/gi)||[]).map(t=>normalized(t)))].sort()}
function canMerge(a,b){
 if(canonicalURL(a.url)===canonicalURL(b.url))return true;
 if(!a.date||!b.date||Math.abs(dateMs(a.date)-dateMs(b.date))>36*3600000)return false;
 const entityA=getEntity(a.title+' '+(a.description||'')),entityB=getEntity(b.title+' '+(b.description||''));
 if(entityA&&entityB&&entityA!==entityB)return false;
 const typA=getEventType(a.title),typB=getEventType(b.title);
 if(typA!==typB)return false;
 const na=getNumbers(a.title),nb=getNumbers(b.title);
 if(na.length&&nb.length&&na.join('|')!==nb.join('|'))return false;
 // Different languages without sufficient same-event evidence remain separate, never silently merged.
 return nearTitle(a.title,b.title)&&(!entityA||!entityB||entityA===entityB);
}
function priority(title,tier,description=''){
 const t=normalized(title+' '+description),head=normalized(title);
 let score=tier==='official'?2:1,reason=[],event=getEventType(title);
 const check=(p,points,msg)=>{if(p.test(t)){score+=points;reason.push(msg)}};
 check(/suspend|suspendare|insolven|faliment|bankrupt|fraud|default|risc sistemic|preluare|takeover/,6,'重大交易/信用风险');
 check(/interest rate decision|monetary policy decision|decizie de politica monetara|dobanda cheie|key interest rate|rate hike|rate cut/,5,'关键货币决议');
 check(/dividend|profit net|pierdere|rezultate financiare|financial results|earnings|raport trimestrial|raport anual/,3,'财报/分红');
 check(/hidroelectrica|transilvania|romgaz|nuclearelectrica|petrom|pretul petrolului|energy|energie|gaz natural|petrol/,2,'能源/重点公司');
 check(/bvb|bursa de valori|bet index|listare|oferta publica|majorare capital|actionari/,2,'证券市场');
 check(/geopolit|razboi|sanctiun|embargo|tarif|taxe vamale/,3,'政策/外部风险');
 if(tickerPattern.test(title)){score+=2;reason.push('股票/指数')}
 // Speeches discussing monetary policy are not themselves rate decisions.
 if(event==='讲话/评论'){score=Math.min(score,5);reason.push('讲话/评论：不等于新政策')}
 if(!head||head.length<10){score=Math.min(score,4)}
 const level=score>=10?'critical':score>=7?'high':score>=4?'medium':'low';
 return {score,priority:level,reason:[...new Set(reason)].join('、')||'普通资讯',eventType:event};
}
function mergeNews(raw){
 const now=Date.now(),newRows=[],oldById=new Map(articles.map(a=>[a.id,a]));
 const maxAge=14*86400000,revisionIds=new Set();
 for(const item of raw){
  if(!item?.title||!item.url)continue;
  const url=canonicalURL(item.url);if(!url)continue;
  const pub=dateMs(item.dateRaw);
  const incoming={id:url,title:String(item.title).trim(),url,date:Number.isFinite(pub)?new Date(pub).toISOString():null,
   description:String(item.description||'').slice(0,450),guid:String(item.guid||''),sourceUrl:String(item.sourceUrl||''),source:item.source||'未知来源',sourceId:item.sourceId||'',tier:item.tier||'media'};
  const similar=newRows.find(x=>canMerge(x,incoming));
  if(similar){
   if(!similar.sources.some(x=>x.url===url))similar.sources.push({source:incoming.source,url});
   // Retain original reporter URL; avoid silently changing a reviewed item.
   if(incoming.tier==='official'&&similar.tier!=='official'&&!similar.verified){similar.source=incoming.source;similar.tier='official'}
   continue;
  }
  const prev=oldById.get(url)||articles.find(x=>canMerge(x,incoming));
  const revised=!!(prev&&canonicalURL(prev.url)===url&&(
    normalized(prev.title)!==normalized(incoming.title)||
    (prev.description&&incoming.description&&normalized(prev.description)!==normalized(incoming.description))));
  if(revised)revisionIds.add(prev.id);
  const score=priority(incoming.title,incoming.tier,incoming.description);
  const verified=!!(prev?.verified&&!revised&&prev.reviewNote?.length>=8&&prev.reviewChecks?.every(Boolean));
  const itemOut={...incoming,id:prev?.id||url,score:score.score,priority:score.priority,reason:score.reason,eventType:score.eventType,
   firstSeen:prev?.firstSeen||new Date(now).toISOString(),lastFetchedAt:new Date(now).toISOString(),fetchStatus:'current',verified,verifiedAt:verified?prev.verifiedAt:null,
   zhTitle:revised?'':(prev?.zhTitle||''),translationStatus:revised?'pending':(prev?.translationStatus||'pending'),translationAttemptedAt:revised?null:(prev?.translationAttemptedAt||null),
   reviewNote:verified?prev.reviewNote:'',reviewChecks:verified?prev.reviewChecks:[false,false,false],
   originalExcerpt:revised?null:(prev?.originalExcerpt||null),excerptLoadedAt:revised?null:(prev?.excerptLoadedAt||null),
   revision:revised,revisionAt:revised?new Date(now).toISOString():prev?.revisionAt||null,
   sources:[...new Map([...(prev?.sources||[]),{source:incoming.source,url}].map(x=>[x.url,x])).values()]};
  newRows.push(itemOut);
 }
 for(const old of articles){if(!newRows.some(x=>x.id===old.id)&&now-dateMs(old.firstSeen||old.date||now)<maxAge)newRows.push({...old,fetchStatus:'cached'})}
 newRows.sort((a,b)=>(dateMs(b.date)||0)-(dateMs(a.date)||0));articles=newRows.slice(0,450);
 if(revisionIds.size){for(const d of Object.values(drafts))if(d.selected?.some(id=>revisionIds.has(id))){d.approved=false;d.published=false;d.approvedAt=null;}saveDraft();}
 store.set(KEYS.news,articles);
 const fresh=[];
 for(const a of articles){if(a.fetchStatus!=='current')continue;if(seen.has(a.id)&&!revisionIds.has(a.id))continue;seen.add(a.id);
  if(baseline&&['critical','high'].includes(a.priority)&&a.date&&now-dateMs(a.date)>=0&&now-dateMs(a.date)<=3*3600000)fresh.push(a)}
 seen=new Set([...seen].slice(-2000));store.set(KEYS.seen,[...seen]);
 if(!baseline){baseline=true;store.set(KEYS.first,true)}else if(fresh.length)urgentAlert(fresh);
 return {total:articles.length,added:newRows.length,urgent:fresh.length,revisions:revisionIds.size};
}
function timedAlert(e){const title=`${e.slot.title} · ${e.type}时间已到`;showToast(title);try{if('Notification'in window&&Notification.permission==='granted')new Notification('BVB资料包时间提醒',{body:`${e.date} ${e.type} ${e.type==='备料'?e.slot.prep:e.slot.pub}（罗马尼亚时间）｜${e.slot.title}`,tag:`slot_${e.date}_${e.slot.id}_${e.type}`})}catch{}}
function urgentAlert(items){const n=items.length;showToast(`发现 ${n} 条新重大候选资讯，请打开原文人工核实`);if(!notifications)return;try{if('Notification'in window&&Notification.permission==='granted')new Notification(`BVB资讯助手：${n}条新重大消息候选`,{body:items.slice(0,2).map(x=>x.title).join('；'),tag:'bvb-alert',silent:false})}catch{};try{const A=window.AudioContext||window.webkitAudioContext;if(A){const c=new A(),o=c.createOscillator(),g=c.createGain();o.type='sine';o.frequency.value=760;g.gain.value=.07;o.connect(g);g.connect(c.destination);o.start();setTimeout(()=>{o.stop();c.close()},240)}}catch{}}
function renderFreshStatus(){
 const current=articles.filter(a=>a.fetchStatus==='current').length,cached=articles.length-current;
 const success=sources.filter(s=>s.state==='ok').length;
 const date=lastFetch?formatRODate(lastFetch):'无';
 $('freshStatus').textContent=`本次采集：${date} · ${success}/${sources.length||5} 个源成功 · 新取得 ${current} 条 · 历史缓存 ${cached} 条。失败来源可能仍有旧新闻，旧新闻不算本次获取。`;
 $('freshStatus').classList.toggle('has-current',current>0);
}
function sourceLang(a){return ['ecb','fed','bls','romania-insider','bloomberg','reuters','wsj-cn'].includes(a.sourceId)?'en':'ro'}
async function translateOne(a,force=false){
 if(!a||!connected)return false;
 if(a.zhTitle&&!force)return true;
 if(!force&&a.translationStatus==='failed'&&Date.now()-(dateMs(a.translationAttemptedAt)||0)<3600000)return false;
 if(a.translationStatus==='busy')return false;
 a.translationStatus='busy';a.translationAttemptedAt=new Date().toISOString();
 try{
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),11500);
  let response;
  try{response=await fetch('/api/translate?lang='+sourceLang(a)+'&text='+encodeURIComponent(a.title),{signal:controller.signal,cache:'no-store'})}finally{clearTimeout(timeout)}
  if(!response.ok)throw Error('HTTP '+response.status);
  const obj=await response.json();
  if(obj.status!=='ok'||typeof obj.translated!=='string'||!/[\u4e00-\u9fff]/.test(obj.translated))throw Error(obj.error||'中文翻译未返回');
  a.zhTitle=obj.translated.trim();a.translationStatus='ok';
 }catch(err){a.translationStatus='failed';translationFailures++;a.translateError=String(err.message||err).slice(0,130)}
 store.set(KEYS.news,articles);renderNews();
 return a.translationStatus==='ok';
}
async function translateHeadlines(force=false){
 if(translating||!connected)return;
 if(!translationEnabled&&!force)return;
 translating=true;
 try{
  const candidates=articles.filter(a=>(force||a.fetchStatus==='current')&&!a.zhTitle&&a.title&&a.title.length<=320).sort((a,b)=>(dateMs(b.date)||0)-(dateMs(a.date)||0));
  const count=force?Math.min(14,candidates.length):Math.min(8,candidates.length);
  for(const a of candidates.slice(0,count)){
   if(!translationEnabled&&!force)break;
   await translateOne(a,force);
  }
  if(translationFailures&&force)showToast('部分新闻机翻不可用，已保留原文；可核验后人工填写资料包');
 }finally{translating=false}
}
function renderSources(){if(!sources.length){$('sourceStrip').textContent=connected?'尚未取得资讯源状态':'未连接本地采集服务';return}
 $('sourceStrip').innerHTML=sources.map(s=>`<button type="button" class="source-chip ${s.state==='ok'?'ok':'fail'}" data-source="${escapeHtml(s.id)}" title="点击查看来源状态和失败原因">${s.state==='ok'?'●':'○'} ${escapeHtml(s.name)} ${s.state==='ok'?s.count+'条':'失败（查看原因）'}</button>`).join('');
 $('sourceStrip').querySelectorAll('[data-source]').forEach(el=>el.onclick=()=>{const x=sources.find(s=>s.id===el.dataset.source);if(!x)return;const message=`${x.name}：${x.state==='ok'?`成功获取 ${x.count} 条。`:'本次采集失败。'}${x.message||''}。RSS为机器读取的XML，不需要人工打开阅读。`;showToast(message);$('sourceDetails').textContent=message;$('sourceDetails').hidden=false;});}
function renderNews(){
 const scrollY=$('newsList').scrollTop;
 const draft=getDraft(),selectedSet=new Set(draft.selected||[]),query=normalized(newsSearch);
 let list=articles.filter(a=>{if(onlyFresh&&a.fetchStatus!=='current')return false;if(query&&!normalized(`${a.title} ${a.source} ${a.description||''}`).includes(query))return false;
  if(newsFilter==='priority'&&!['high','critical'].includes(a.priority))return false;
  if(newsFilter==='pending'&&a.verified)return false;if(newsFilter==='approved'&&!a.verified)return false;
  if(newsFilter==='selected'&&!selectedSet.has(a.id))return false;return true});
 const priorityOrder={critical:4,high:3,medium:2,low:1};list.sort((a,b)=>(b.fetchStatus==='current')-(a.fetchStatus==='current')||priorityOrder[b.priority]-priorityOrder[a.priority]||(dateMs(b.date)||0)-(dateMs(a.date)||0));
 $('newsCount').textContent=articles.length;
 $('urgentCount').textContent=articles.filter(a=>a.fetchStatus==='current'&&['critical','high'].includes(a.priority)&&!a.verified&&a.date&&Date.now()-dateMs(a.date)<86400000).length+' 条重要待核验';
 $('newsList').innerHTML=list.length?list.slice(0,150).map(a=>
 `<div class="newsitem ${['critical','high'].includes(a.priority)?'urgentitem':''} ${a.fetchStatus==='current'?'':'cached-item'}">
 <div class="article-top"><span class="badge ${a.priority}">${{critical:'重大候审',high:'重点候审',medium:'常规关注',low:'普通'}[a.priority]}</span><span class="article-source">${escapeHtml(a.source)} · ${escapeHtml(formatRODate(a.date))}</span></div>
 ${a.zhTitle?`<div class="article-translation">${escapeHtml(a.zhTitle)} <small>自动机翻·未经事实核验</small></div><div class="article-original"><span class="subtle">罗马尼亚语/英语原文：</span> ${escapeHtml(a.title)}</div>`:`<div class="article-title">${escapeHtml(a.title)}</div>${a.translationStatus==='failed'?'<div class="article-transfailed">在线中文机翻暂不可用，保留原文</div>':''}`}
 <div class="article-flags"><span class="fresh-pill ${a.fetchStatus==='current'?'':'cached'}">${a.fetchStatus==='current'?'本次采集':'历史缓存（非本次采集）'}</span>${a.fetchStatus!=='current'&&a.lastFetchedAt?`<span>上次成功见到：${escapeHtml(formatRODate(a.lastFetchedAt))}</span>`:''}</div>
 ${a.description?`<div class="article-summary">来源摘要：${escapeHtml(a.description)}</div>`:''}
 <div class="article-flags"><span>类型：${escapeHtml(a.eventType||'未分类')}</span>${a.sources?.length>1?`<span>${a.sources.length}个相关来源（需确认同事件）</span>`:''}${a.revision?'<span class="needs">来源内容已更新，须重新核验</span>':''}</div>
 <div class="article-sub"><span>${escapeHtml(a.reason)} · 候审评分${a.score}</span><span>${a.verified?'<b style="color:#287556">已记录人工核验</b>':'未经人工核验'}</span></div>
 <div class="article-actions"><a class="actionlink" target="_blank" rel="noopener noreferrer" href="${escapeHtml(a.url)}">↗ 打开原文</a>
 <button class="actionbtn" data-action="translate" data-id="${escapeHtml(a.id)}">${a.zhTitle?'↻ 重新翻译':'文→中 翻译标题'}</button>
 <button class="actionbtn ${a.verified?'approved':''}" data-action="verify" data-id="${escapeHtml(a.id)}">${a.verified?'✓ 查看/复核记录':'核验原文及事实'}</button>
 <button class="actionbtn ${selectedSet.has(a.id)?'selected':''}" data-action="select" data-id="${escapeHtml(a.id)}">${selectedSet.has(a.id)?'✓ 已加入本节点':'＋ 加入本节点'}</button></div></div>`).join(''):
 `<div class="empty"><div class="emptyicon">⌁</div><b>没有符合条件的新闻</b><p>${articles.length?'可切换过滤条件。':'请先启动本地服务器并采集，缺失资讯时不会填充虚构新闻。'}</p></div>`;
 $('newsList').scrollTop=scrollY;
 $('newsList').querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>{
  const a=articles.find(x=>x.id===b.dataset.id);if(!a)return;
  if(b.dataset.action==='verify'){openReview(a);return}
  if(b.dataset.action==='translate'){translateOne(a,true).then(ok=>showToast(ok?'已生成机翻，仅供参考':'翻译服务暂不可用，原文保留'));return}
  const d=getDraft();if(!a.verified){showToast('必须先完成人工原文核验并保存审核依据');return}
  if(d.selected.includes(a.id))d.selected=d.selected.filter(x=>x!==a.id);else d.selected.push(a.id);
  invalidate(d);renderNews();updatePreview();
 });
}
function openReview(a){
 activeReviewId=a.id;$('verifyTitle').textContent=a.title;
 $('verifyMeta').textContent=`来源：${a.source}｜原文发布日期：${a.date?formatRODate(a.date):'未知'}｜事件类别：${a.eventType||'未分类'}｜${a.revision?'有修订，需复核':'未标记修订'}`;
 $('openOriginal').href=a.url;
 $('originalPreview').textContent=a.description?`RSS摘要（不代表完整正文）：\n${a.description}`:'尚未取得正文摘要，请打开原始网页查阅。';
 $('checkSource').checked=!!a.reviewChecks?.[0];$('checkFacts').checked=!!a.reviewChecks?.[1];$('checkChange').checked=!!a.reviewChecks?.[2];
 $('verifyNote').value=a.reviewNote||'';$('revokeVerified').disabled=!a.verified;
 $('verifyDialog').showModal();
}
async function fetchArticle(){
 const a=articles.find(x=>x.id===activeReviewId);if(!a)return;
 $('fetchOriginal').disabled=true;$('originalPreview').textContent='正在提取来源网页正文……';
 try{const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),16000);let r;
  try{r=await fetch('/api/article?url='+encodeURIComponent(a.url),{signal:ctl.signal,cache:'no-store'})}finally{clearTimeout(tm)}
  const data=await r.json();if(!r.ok)throw new Error(data.error||'HTTP '+r.status);
  $('originalPreview').textContent=`【自动提取时间】${new Date(data.fetchedAt).toLocaleString('zh-CN')}\n【原文摘录，未经核验】\n${data.content}`;
  a.excerptLoadedAt=data.fetchedAt;a.originalExcerpt=data.content;store.set(KEYS.news,articles);
 }catch(err){$('originalPreview').textContent=`无法提取正文：${err.message}\n请手动打开原文网页核对。PDF、JS动态网页或访问受限内容不会自动猜测。`}
 finally{$('fetchOriginal').disabled=false}
}
function saveReview(){
 const a=articles.find(x=>x.id===activeReviewId);if(!a)return;
 const checks=[$('checkSource').checked,$('checkFacts').checked,$('checkChange').checked],note=$('verifyNote').value.trim();
 if(checks.some(x=>!x)){showToast('必须完成3项核验确认');return}
 if(note.length<8){showToast('请填写至少8个字的人工核验依据');return}
 a.verified=true;a.verifiedAt=new Date().toISOString();a.reviewNote=note;a.reviewChecks=checks;a.revision=false;
 store.set(KEYS.news,articles);for(const d of Object.values(drafts))if(d.selected?.includes(a.id)){d.approved=false;d.approvedAt=null;d.published=false;}saveDraft();
 $('verifyDialog').close();renderNews();updatePreview();showToast('人工审核依据已保存（系统不自动保证事实真实）');
}
function revokeReview(){const a=articles.find(x=>x.id===activeReviewId);if(!a)return;
 a.verified=false;a.verifiedAt=null;a.reviewNote='';a.reviewChecks=[false,false,false];
 for(const d of Object.values(drafts))if(d.selected?.includes(a.id)){d.approved=false;d.approvedAt=null;d.published=false;}
 store.set(KEYS.news,articles);saveDraft();$('verifyDialog').close();renderNews();updatePreview();showToast('已撤销核验，相关稿件需重新审核')}
function applyQuote(){if(!quote||quote.state!=='ok'||!Number.isFinite(Number(quote.value))||!Number.isFinite(dateMs(quote.marketTime))){showToast('报价接口没有取得可验证BET数据，请自行从BVB页面核验');return}const draft=getDraft();draft.quoteSource={marketTime:quote.marketTime,value:quote.value,url:quote.url};draft.fields.bet=`${Number(quote.value).toLocaleString('en-US')}点（BVB WebDelayed；${quote.marketTime||'行情时间未知，须人工确认'}）`;draft.fields.change=`${quote.change>0?'+':''}${quote.change}%（BVB接口；需人工确认）`;draft.fields.source=[cleanField(draft.fields.source),quote.url].filter(Boolean).join('\n');invalidate(draft);renderEditor();$('fieldDetails').open=true;showToast('已引用报价，请确认实际行情时间、来源与访问权限')}
function applyNews(){const d=getDraft(),ids=d.selected||[],list=ids.map(id=>articles.find(a=>a.id===id)).filter(a=>a?.verified);if(!list.length){showToast('请先人工核验资讯，然后点击「加入本节点」');return}d.fields.headline=d.fields.headline||list[0].title;if(list[1])d.fields.headline2=d.fields.headline2||list[1].title;d.fields.source=[cleanField(d.fields.source),...list.map(a=>a.url)].filter(Boolean).filter((x,i,all)=>all.indexOf(x)===i).join('\n');invalidate(d);renderEditor();$('fieldDetails').open=true;showToast(`已将 ${list.length} 条经过人工核验的资讯引用到资料包`)}
async function refresh(manual=false){if(refreshing){while(refreshing)await new Promise(resolve=>setTimeout(resolve,100));return refresh(manual);}if(!connected){if(manual)showToast('本地采集服务未连接。请双击「启动_BVB资讯助手.cmd」');await checkServer();if(!connected)return false}refreshing=true;$('refreshBtn').disabled=true;$('refreshBtn').textContent='正在从新闻源采集…';try{const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),240000);let r;try{r=await fetch('/api/refresh',{cache:'no-store',signal:ctrl.signal})}finally{clearTimeout(timer)}if(!r.ok)throw new Error('采集HTTP '+r.status);const data=await r.json();if(!Array.isArray(data.articles)||!Array.isArray(data.sources))throw new Error('来源数据格式异常');sources=data.sources;quote=data.quote||null;lastFetch=data.fetchedAt||new Date().toISOString();const res=mergeNews(data.articles);renderSources();renderFreshStatus();renderNews();renderQuote();updatePreview();$('reviewBox').checked=!!getDraft().approved;$('lastSync').textContent=`最后采集：${formatRODate(lastFetch)} · ${sources.filter(s=>s.state==='ok').length}/${sources.length} 源成功 · 节点资料采集（网页打开时）`;if(manual)showToast(`采集完成：${sources.filter(s=>s.state==='ok').length}个源成功，本次${articles.filter(x=>x.fetchStatus==='current').length}条；其余为历史缓存`);
  translateHeadlines(false).catch(e=>console.warn('翻译请求：',e.message));return true}catch(e){$('lastSync').textContent=`采集失败：${e.message} · 仅能查看历史缓存`;for(const a of articles){a.fetchStatus='cached';if(a.translationStatus==='busy')a.translationStatus='pending';}renderFreshStatus();renderNews();if(manual)showToast(`采集失败：${e.message}`);return false}finally{refreshing=false;$('refreshBtn').disabled=false;$('refreshBtn').textContent='↻ 立即采集'}}
function renderQuote(){if(quote?.state==='ok'&&Number(quote.value)>0){$('betValue').textContent=Number(quote.value).toLocaleString('en-US');$('betInfo').textContent=`${quote.change>0?'+':''}${quote.change}% · ${quote.marketTime||'时间未返回'} · 需核验 · 非保证实时`;}else{$('betValue').textContent='未获取';$('betInfo').textContent=(quote?.note||'行情接口需要可用性与授权核验')+' · 点击“查看BVB官方行情”人工核对'}}
async function checkServer(){try{const ctl=new AbortController(),time=setTimeout(()=>ctl.abort(),2500);let r;try{r=await fetch('/api/status',{cache:'no-store',signal:ctl.signal})}finally{clearTimeout(time)}connected=r.ok&&(await r.json()).ok===true}catch{connected=false}$('connPill').classList.toggle('online',connected);$('connPill').classList.toggle('offline',!connected);$('connPill').innerHTML=`<i></i>${connected?'本地资讯服务已连接':'本地资讯服务未连接'}`;if(!connected){$('lastSync').textContent='服务离线：需要双击启动 CMD 才能自动采集 · 时钟和模板可离线使用';renderSources()}}
async function copy(){let v=buildText();try{await navigator.clipboard.writeText(v);showToast('已复制当前资料包')}catch{const t=document.createElement('textarea');t.value=v;t.style.position='fixed';t.style.opacity=0;document.body.appendChild(t);t.select();let ok=document.execCommand('copy');t.remove();showToast(ok?'已复制当前资料包':'浏览器阻止复制，请手动选中文案复制')}}
function download(filename,mime,content){const u=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),3000)}
function stem(){return `BVB_${lastDate}_${activeId}`}
function bind(){
 bindCollection();
 $('closeVerify').onclick=()=>$('verifyDialog').close();$('fetchOriginal').onclick=fetchArticle;$('saveVerified').onclick=saveReview;$('revokeVerified').onclick=revokeReview;
 document.querySelectorAll('[data-nodes]').forEach(el=>el.onclick=()=>{nodeView=el.dataset.nodes;document.querySelectorAll('[data-nodes]').forEach(b=>b.classList.toggle('active',b===el));renderTimeline()});$('autoNode').onchange=e=>{auto=e.target.checked;if(auto){const ro=getRO();const slot=todaySlots(ro.day).filter(s=>minOf(s.prep)<=ro.hour*60+ro.minute).at(-1)||SLOTS[0];selectSlot((slot||SLOTS[0]).id,false)}};
 $('autoTranslate').checked=translationEnabled;
 $('autoTranslate').onchange=e=>{translationEnabled=e.target.checked;store.set(KEYS.machineTranslation,translationEnabled);if(translationEnabled)translateHeadlines(false);showToast(translationEnabled?'已允许通过第三方翻译公开新闻标题':'已停止自动向第三方翻译公开标题')};
 $('onlyFresh').onchange=e=>{onlyFresh=e.target.checked;renderNews()};
 $('translateVisible').onclick=()=>translateHeadlines(true);
 $('newsSearch').oninput=e=>{newsSearch=e.target.value;renderNews()};$('newsFilter').onchange=e=>{newsFilter=e.target.value;renderNews()};$('refreshBtn').onclick=()=>refresh(true);$('quoteBtn').onclick=applyQuote;$('assembleBtn').onclick=applyNews;
 $('reviewBox').onchange=e=>{const d=getDraft();if(!e.target.checked){invalidate(d);updatePreview();return}const issues=reviewErrors();if(issues.length){e.target.checked=false;showToast(`还有${issues.length}类资料或证据问题，不能标记审核通过`);updatePreview();return}if(!window.confirm('你确认已经逐条核对原始链接、时间戳、行情数字和措辞？\n请注意：勾选只记录人工审核，不代表系统自动证实数据。')){e.target.checked=false;return}d.approved=true;d.approvedAt=new Date().toISOString();saveDraft();updatePreview();showToast('已记录人工审核完成')};
 $('copyBtn').onclick=copy;$('exportTxt').onclick=()=>{download(stem()+'.txt','text/plain;charset=utf-8',buildText());showToast('已导出TXT')};$('exportJson').onclick=()=>{download(stem()+'.json','application/json;charset=utf-8',JSON.stringify(currentBundle(),null,2));showToast('已导出全面素材，待导演筛选')};
 $('exportNews').onclick=()=>{download('BVB_news_'+getRO().date+'.json','application/json;charset=utf-8',JSON.stringify({exportedAt:new Date().toISOString(),sourceStatus:sources,articles,warning:'此台账的自动风险评级不等于人工事实核验'},null,2));showToast('已导出资讯台账')};
 $('markPublished').onclick=()=>{const d=getDraft();if(!d.approved||reviewErrors().length){showToast('尚未满足发布门禁，请检查字段及审核记录');return}if(!window.confirm('确认你已在外部渠道实际发布这份内容？（本工具不会替你发送消息）'))return;d.published=true;d.publishedAt=new Date().toISOString();saveDraft();updatePreview();renderTimeline();showToast('已记录人工发布状态，没有向WhatsApp自动发送')};
 $('notifyBtn').onclick=async()=>{if(notifications){notifications=false;$('notifyBtn').textContent='◉ 开启重要资讯提醒';showToast('已关闭本页面的弹窗提醒');return}if(!('Notification'in window)){showToast('浏览器不支持系统通知，网页内提醒仍可使用');notifications=true;$('notifyBtn').textContent='✓ 已启用页面提醒';return}try{const permission=await Notification.requestPermission();notifications=permission==='granted';$('notifyBtn').textContent=notifications?'✓ 重要资讯提醒已开启':'◉ 开启重要资讯提醒';showToast(notifications?'已授权浏览器通知；仅在网页运行时检查':'未取得通知权限，可继续查看站内提示')}catch{showToast('未能申请通知权限')}}}

const CORE=window.BVB_COLLECTION;
const CKEY='bvb_v4_collections',MKEY='bvb_v4_metrics',CTXKEY='bvb_v4_context';
let collections=store.get(CKEY,{}),metricData=store.get(MKEY,{metrics:[]}),contexts=store.get(CTXKEY,{}),scheduledEnabled=store.get('bvb_v4_scheduled',true),previousCollectionTime=store.get('bvb_v5_last_tick',null),collectQueue=Promise.resolve();
// Persisted RUNNING records from an interrupted browser session are not successful harvests.
for(const r of Object.values(collections))if(['RUNNING','QUEUED'].includes(r.status)){r.status='FAILED';r.retryAt=0;r.error='上次页面中断，尚未完成';}
function currentBundle(){
 const slot=SLOTS.find(s=>s.id===activeId)||SLOTS[0];
 const own=Object.values(collections).filter(r=>r.date===lastDate&&r.nodeId===slot.id).sort((a,b)=>String(a.completedAt||a.startedAt).localeCompare(String(b.completedAt||b.startedAt))).at(-1);
 const base=own?.bundle;
 const b=CORE.bundle({node:slot,date:lastDate,articles:base?.news_candidates||articles,sources:base?.source_status||sources,metrics:base?.metrics||metricData.metrics||[],context:contexts[activeKey()]||'',collection:own?{status:own.status,stage:own.stage,scheduledAt:own.scheduledAt,completedAt:own.completedAt,late:own.late,error:own.error||null}:null});
 b.node_collected_at=base?.collected_at||null;b.exported_at=new Date().toISOString();b.collected_at=base?.collected_at||null;b.data_view=base?'IMMUTABLE_NODE_SNAPSHOT':'UNSNAPSHOTTED_CURRENT_CACHE';b.quote=base?.quote||quote||null;b.manual_fields={...getDraft().fields};return b;
}
function buildText(){return CORE.text(currentBundle());}
function collectionUI(){
 const own=Object.values(collections).filter(r=>r.date===lastDate&&r.nodeId===activeId).at(-1);
 $('collectionStatus').textContent=own?`${own.status} · ${own.stage} · ${own.completedAt||own.startedAt}${own.late?' · 延迟补采（非计划时刻行情）':''}${own.error?' · '+own.error:''}`:'尚未采集此节点；自动采集需保持页面与服务运行';
 $('metricStatus').textContent=`已导入 ${(metricData.metrics||[]).length} 项指标；未提供数据列为缺失，按观测时间检查时效。`;
 $('contextInput').value=contexts[activeKey()]||'';
}

async function collectMarketMetrics(node){
 const keys=node.groups.includes('international')?['SP500','NASDAQ','DAX','FTSE','SP_FUTURE','NQ_FUTURE','US10Y','DXY','USDRON','EURRON']:[];
 if(node.groups.includes('energy'))keys.push('BRENT','TTF');
 for(const key of keys){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
  try{
   const response=await fetch('/api/market?key='+encodeURIComponent(key),{cache:'no-store',signal:controller.signal});const data=await response.json();
   const metric=data.metric||{id:'auto-'+key,group:['BRENT','TTF'].includes(key)?'energy':'international',name:key,asset:key,value:null,unit:'',observed_at:null,source_url:'',verification_status:'MISSING',error:data.error||'行情接口未返回数据'};
   // Validate quote shape; malformed provider responses become missing rather than aborting other assets.
   CORE.validateImport({metrics:[metric]});metricData.metrics=(metricData.metrics||[]).filter(m=>m.id!==metric.id);metricData.metrics.push(metric);
  }catch(e){const id='auto-'+key;metricData.metrics=(metricData.metrics||[]).filter(m=>m.id!==id);metricData.metrics.push({id,group:['BRENT','TTF'].includes(key)?'energy':'international',name:key,value:null,verification_status:'MISSING',error:e.message});}
  finally{clearTimeout(timer);}
 }
 store.set(MKEY,metricData);
}

async function collectEvent(evt){
 const rec={key:evt.key,nodeId:evt.node.id,date:evt.date,stage:evt.stage,scheduledAt:evt.scheduledAt,late:evt.late||Date.now()-Date.parse(evt.scheduledAt)>60000,status:'RUNNING',startedAt:new Date().toISOString()};
 collections[evt.key]=rec;store.set(CKEY,collections);collectionUI();
 try{
  const internal=evt.node.mode==='INTERNAL';
  if(!internal){const ok=await refresh(false);if(!ok)throw Error('服务离线或网络采集失败');}
  if(!internal)await collectMarketMetrics(evt.node);
  const context=contexts[`${evt.date}/${evt.node.id}`]||'';
  rec.bundle=CORE.bundle({node:evt.node,date:evt.date,articles:articles.map(a=>internal?{...a,fetchStatus:'cached'}:a),sources:internal?sources.map(s=>({...s,internalReuse:true})):sources,metrics:metricData.metrics||[],context,collection:{stage:evt.stage,late:rec.late}});
  rec.bundle.quote=quote?{...quote,internalReuse:internal}:null;
  rec.completedAt=new Date().toISOString();rec.bundle.collected_at=rec.completedAt;rec.bundle.collection_status={stage:evt.stage,late:rec.late,startedAt:rec.startedAt,completedAt:rec.completedAt};rec.status=internal?'INTERNAL_READY':(sources.some(s=>s.state==='ok')||(rec.bundle.metrics||[]).some(m=>m.value!==null&&m.data_state==='AS_OF_TIMESTAMP'))?'COLLECTED_PARTIAL':'FAILED';
  if(rec.status==='FAILED')throw Error('新闻源与当前节点所需参考指标未取得有效更新；旧缓存不算本轮新采集');
 }catch(e){rec.status='FAILED';rec.error=e.message;rec.retryAt=Date.now()+60000;}
 // Keep bounded local records; exports preserve complete snapshots before pruning.
 const dates=[...new Set(Object.values(collections).map(r=>r.date))].sort();for(const r of Object.values(collections))if(dates.length>7&&r.date<dates.at(-7))delete collections[r.key];
 store.set(CKEY,collections);collectionUI();if(evt.node.id===activeId)updatePreview();
}
function runCollectionClock(now){
 if(!scheduledEnabled){previousCollectionTime=now.getTime();return;}
 const due=CORE.due(now,previousCollectionTime,collections);previousCollectionTime=now.getTime();store.set('bvb_v5_last_tick',previousCollectionTime);
 for(const evt of due){collections[evt.key]={...evt,node:undefined,nodeId:evt.node.id,status:'QUEUED'};collectQueue=collectQueue.then(()=>collectEvent(evt)).catch(e=>console.error('节点采集',e));}
}
function bindCollection(){
 $('scheduledCollect').checked=scheduledEnabled;$('scheduledCollect').onchange=e=>{scheduledEnabled=e.target.checked;store.set('bvb_v4_scheduled',scheduledEnabled);previousCollectionTime=null;};
 $('contextInput').oninput=e=>{contexts[activeKey()]=e.target.value;store.set(CTXKEY,contexts);updatePreview();};
 $('collectNode').onclick=()=>{const node=SLOTS.find(s=>s.id===activeId);const now=new Date();const evt={key:`${lastDate}/${node.id}/MANUAL/${now.toISOString()}`,node,date:lastDate,stage:'MANUAL',scheduledAt:now.toISOString(),late:false};collectQueue=collectQueue.then(()=>collectEvent(evt));};
 $('importMetrics').onclick=()=>$('metricFile').click();
 $('metricFile').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;if(f.size>2*1024*1024)throw Error('文件超过2MB');const imported=CORE.validateImport(JSON.parse(await f.text()));const ids=new Set(imported.metrics.map(m=>m.id));metricData={metrics:[...(metricData.metrics||[]).filter(m=>!ids.has(m.id)),...imported.metrics]};store.set(MKEY,metricData);collectionUI();updatePreview();showToast('已导入有来源的指标资料')}catch(e){showToast('导入失败：'+e.message)}finally{$('metricFile').value='';}};
 $('metricTemplate').onclick=()=>download('BVB-metrics-template.json','application/json',JSON.stringify({metrics:[{id:'brent-latest',group:'energy',name:'Brent',asset:'Brent',contract:null,value:null,unit:'USD/barrel',observed_at:null,source_url:'',baseline:null,period:'INTRADAY',verification_status:'MISSING',verification_note:''}]},null,2));
 $('exportCollections').onclick=()=>download(`BVB-collections-${lastDate}.json`,'application/json',JSON.stringify({story_date:lastDate,timezone:TZ,records:Object.values(collections).filter(r=>r.date===lastDate)},null,2));
}

async function init(){
 // v2 compatibility: a prior one-click verification never counts as a v3 evidence record.
 let migrated=false;
 for(const a of articles)if(a.verified&&(!(a.reviewNote||'').trim()||!Array.isArray(a.reviewChecks)||a.reviewChecks.length!==3||a.reviewChecks.some(x=>!x))){a.verified=false;a.verifiedAt=null;a.reviewNote='';a.reviewChecks=[false,false,false];migrated=true;}
 if(migrated){store.set(KEYS.news,articles);for(const d of Object.values(drafts)){d.approved=false;d.approvedAt=null;d.published=false;}saveDraft();}
 // Cached records from the previous browser session are never silently treated as this session's live harvest.
 for(const a of articles){a.fetchStatus='cached';if(a.translationStatus==='busy')a.translationStatus='pending';}
 lastDate=getRO().date;const ro=getRO(),slots=todaySlots(ro.day),minute=ro.hour*60+ro.minute,cur=slots.filter(s=>minOf(s.prep)<=minute).at(-1)||SLOTS[0];bind();selectSlot(cur.id,false);renderSources();renderFreshStatus();renderNews();clock();setInterval(clock,1000);await checkServer();if(connected&&ro.day!==0&&ro.day!==6&&ro.hour<19)refresh(false)}
init().catch(err=>{console.error(err);showToast('初始化错误：'+String(err.message||err))});
window.BVB_TEST={currentBundle,collectEvent,runCollectionClock,getRO,groupOf,todaySlots,zonedTs,priority,nearTitle,canonicalURL,upcomingEvent,buildText,canMerge,getEventType,getEntity,mergeNews,reviewErrors,refresh,openReview,translateOne,translateHeadlines,renderFreshStatus};
})();
