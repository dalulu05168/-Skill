"""Responsive, standalone writing module UI in the same localhost finance workspace."""
PAGE = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>交易中心 · 65人统一交易与人物工作台</title><style>
:root{font:14px/1.6 Inter,"Microsoft YaHei",system-ui,sans-serif;color:#252629;background:#f4f4f5}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(140deg,#fafafa,#f2f3f5 62%,#f7f1e5);min-height:100vh}
a{color:#826022;text-decoration:none}.app{max-width:1440px;margin:auto;padding:25px clamp(16px,2.5vw,40px) 55px}
.top{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #dedfe2;padding:0 0 18px}
.brand{font-weight:800;font-size:23px;letter-spacing:.04em}.brand span{color:#a27d39}.sub{font-size:11px;letter-spacing:.12em;color:#a27d39}
.nav{display:flex;flex-wrap:wrap;gap:7px}.nav a{padding:10px 14px;border-radius:10px;border:1px solid #e0e0e3;background:white;font-weight:700;font-size:13px}
.nav a.active{background:#2a2c30;color:white}
h1{font-size:clamp(26px,3.5vw,42px);margin:28px 0 7px;letter-spacing:-.025em}h2{font-size:17px;margin:0 0 14px}
p{color:#62656a;margin:6px 0 14px}.muted,small{color:#71757c;font-size:12px}
.layout{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(300px,.9fr);gap:16px;margin-top:22px}
.card{background:#fff;border:1px solid #e2e3e5;border-radius:19px;padding:23px;min-width:0;box-shadow:0 8px 28px #353b4909}
label{font-size:12px;color:#55595f;font-weight:700;display:block;margin:13px 0 6px}
input,select,textarea{width:100%;border:1px solid #dadddf;border-radius:10px;background:#fff;padding:10px 12px;color:#27292c;font:inherit;outline-offset:2px}
textarea{min-height:125px;resize:vertical}#response{min-height:225px}#prompt{min-height:280px;font-size:11px}
.flex{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.flex>*{flex:1;min-width:120px}
.row{display:flex;gap:9px;flex-wrap:wrap;margin:16px 0 0}
button{cursor:pointer;border:0;border-radius:10px;background:#282a2f;color:white;font:700 13px inherit;font-weight:700;padding:11px 16px}
button.alt{background:#f3eddf;color:#80632e}button:disabled{opacity:.55;cursor:wait}
.btnlink{display:inline-block;background:#f2eddf;padding:9px 12px;border-radius:9px}
.note{background:#fbf7ed;color:#765d35;border:1px solid #ebe1ce;border-radius:11px;padding:11px;font-size:12px}
.status{border-left:3px solid #b18a48;padding-left:12px;margin:15px 0;color:#44474b;white-space:pre-wrap}
.people{max-height:240px;overflow-y:auto;border:1px solid #e7e8e9;border-radius:11px;padding:8px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px}
.person{display:flex;align-items:center;gap:8px;border-radius:7px;padding:7px 9px;cursor:pointer;font-size:12px}.person:hover{background:#f6f2e9}.person input{width:16px;flex:none;margin:0}
#peoplelist .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.section{display:none}.section.active{display:block}
.tabs{display:flex;gap:6px;margin:16px 0 4px;flex-wrap:wrap}
.tabs button{background:#edeef0;color:#555;font-size:12px}.tabs button.active{background:#2b2d31;color:#fff}
.item{border-bottom:1px solid #eee;padding:12px 0}.item b{color:#2a2e33}.item small{display:block}
pre{white-space:pre-wrap;word-wrap:break-word;background:#f7f7f8;padding:14px;border-radius:10px;max-height:420px;overflow:auto}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid #b08a42}
@media(max-width:800px){.layout{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.people{grid-template-columns:1fr}.card{padding:17px}}
</style></head><body><div class="app">
<div class="top"><div><div class="brand">NUVEXA <span>· 交易中心</span></div><div class="sub">统一 65 人人物档案 · 独立交易中心模块</div></div>
<nav class="nav" aria-label="主模块"><a href="/">📰 新闻推送</a><a class="active" href="/trading" aria-current="page">💹 交易中心</a><a href="/trade-platform">↗ 外部交易平台</a></nav></div>
<h1>交易中心 · 统一交易与人物工作台</h1>
<p>与新闻审核共享同一套65人人物资料，写作草稿、文档和已确认会话单独保存；不导入旧72人历史。</p>
<div class="note">人物皆为虚构教育演绎。只生成可复制给现有AI的提示词；AI不会在此网页自动运行。检查合格不代表新闻已核实、内容已发送或真实成交。</div>
<div class="tabs" role="tablist" aria-label="交易中心工作区">
<button class="active" data-tab="script">脚本撰写</button><button data-tab="people">65人人物库</button><button data-tab="docs">写作文档</button><button data-tab="history">正式会话与记忆</button></div>
<div class="section active" id="tab-script"><div class="layout">
<section class="card"><h2>01 · 配置模拟场次</h2>
<div class="flex"><div><label for="date">场次日期</label><input type="date" id="date"></div>
<div><label for="node">新闻/课程节点</label><select id="node"></select></div>
<div><label for="source_kind">原话角色</label><select id="source_kind"><option value="assistant">助理</option><option value="professor">教授（仅 RO-10）</option></select></div></div>
<label for="topic">话题名称</label><input id="topic" maxlength="160" value="市场课程互动">
<label for="source_text">助理/教授原话（不改写）</label><textarea id="source_text" maxlength="20000" placeholder="粘贴主持人的真实原话。这里不会自动虚构行情或改写教授内容。"></textarea>
<label for="find">选择需要回应的人物（65人正式档案）</label><input id="find" type="search" placeholder="搜索编号、姓名、职业、城市">
<p class="muted">已选择 <strong id="selected-count">0</strong> 人。可留出沉默角色，不按人数凑发言。</p>
<div class="people" id="peoplelist"><span class="muted">正在读取正式人物库…</span></div>
<div class="row"><button id="make">生成可复制提示词</button><button id="clear" class="alt">清除选择</button></div>
<div class="status" id="make-status">尚未创建草稿。</div>
</section>
<section class="card"><h2>02 · 生成 → 检查 → 确认采用</h2>
<p class="muted">将左侧提示词复制到现有 ChatGPT，取得 JSON 回复后粘贴在下方。只有你点击“确认正式采用”，才进入长期会话记录。</p>
<label for="prompt">完整提示词（包含人物全档案与历史）</label><textarea id="prompt" readonly placeholder="先选择人物并生成提示词"></textarea>
<div class="row"><button class="alt" id="copy">复制提示词</button><a class="btnlink" href="https://chatgpt.com/" target="_blank" rel="noopener noreferrer">打开 ChatGPT · 选择我的GPT ↗</a></div>
<label for="response">AI 返回的 JSON 草稿（messages 数组）</label><textarea id="response" placeholder='{"messages":[{"character_id":"01","name":"Andrei Popescu","gender":"男","role":"新男","text":"..."}]}'></textarea>
<div class="row"><button id="check" class="alt">检查角色与格式</button><button id="adopt">确认正式采用并保存</button></div>
<div class="status" id="review-status">草稿尚未检查。</div><pre id="review-output">校验结果会在这里显示，保存后可在“正式会话与记忆”查看。</pre>
</section></div></div>
<div class="section" id="tab-people"><div class="card"><h2>65人统一人物资料</h2>
<p>本页面通过正式索引与65份完整AI档案交叉核验；只读，无法在写作模块修改源人物身份。</p>
<input type="search" id="people-search" placeholder="搜索人物编号、姓名、职业、城市">
<div id="roster" class="layout"></div><pre id="profile-view">点击人物卡片查看完整档案（只读）。</pre></div></div>
<div class="section" id="tab-docs"><div class="layout">
<section class="card"><h2>写作文档</h2><label for="doc-title">文档标题</label><input id="doc-title" maxlength="160" placeholder="章节或写作备忘">
<label for="doc-body">正文</label><textarea id="doc-body" style="min-height:350px" placeholder="在此记录章节、剧情提纲或作者说明"></textarea>
<div class="row"><button id="save-doc">保存文档</button><button id="new-doc" class="alt">新文档</button></div><div class="status" id="doc-status">文档仅保存在这台电脑的本地写作工作区。</div></section>
<section class="card"><h2>已有文档</h2><div id="docs-list">尚未读取。</div></section></div></div>
<div class="section" id="tab-history"><div class="card"><h2>正式采用的会话</h2>
<p>只有点击“确认正式采用并保存”的内容才记为历史。测试草稿不进入正式会话，且与新闻待审队列独立。</p>
<div class="row"><button id="refresh-history" class="alt">刷新记录</button></div>
<div id="history-list"></div><pre id="history-view">点击记录可查看完整内容。</pre></div></div>
</div><script>
'use strict';
const $=s=>document.querySelector(s);
let people=[],selected=new Set(),draftId=null,verified=false,docs=[],docId=null;
async function api(path,data){
  const opts=data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)};
  const r=await fetch(path,opts),j=await r.json();if(!r.ok)throw Error(j.error||('HTTP '+r.status));return j;
}
function status(selector,msg){$(selector).textContent=msg}
function el(tag,text,klass){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(klass)e.className=klass;return e}
function matches(p,q){return [p.character_id,p.name,p.role,p.occupation,p.city,p.description].join(' ').toLowerCase().includes(q.toLowerCase())}
function paintSelector(){
  const box=$('#peoplelist');box.replaceChildren();
  const filter=$('#find').value.trim();
  for(const p of people.filter(p=>matches(p,filter))){
    const label=el('label',undefined,'person'),cb=document.createElement('input');cb.type='checkbox';cb.checked=selected.has(p.character_id);
    cb.addEventListener('change',()=>{if(cb.checked)selected.add(p.character_id);else selected.delete(p.character_id);$('#selected-count').textContent=selected.size;});
    label.append(cb,el('span',p.character_id+' · '+p.name+' · '+p.role,'name'));box.append(label);
  }
  $('#selected-count').textContent=selected.size;
  if(!box.childElementCount)box.append(el('small','无匹配人物'));
}
function paintRoster(){
  const box=$('#roster');box.replaceChildren();
  for(const p of people.filter(p=>matches(p,$('#people-search').value.trim()))){
    const b=el('button',p.character_id+' · '+p.name+' / '+p.gender+' / '+p.role+' / '+(p.city||''),'alt');
    b.addEventListener('click',async()=>{try{const j=await api('/api/trading/profile?character_id='+encodeURIComponent(p.character_id));$('#profile-view').textContent=JSON.stringify(j.profile,null,2);}catch(e){$('#profile-view').textContent=e.message}});
    box.append(b);
  }
}
async function refreshDocs(){
  const j=await api('/api/trading/state');docs=j.docs;
  const box=$('#docs-list');box.replaceChildren();
  if(!docs.length)box.append(el('p','尚无文档'));
  for(const d of docs){
    const b=el('button',d.title+' · '+d.updated_at,'alt');
    b.style.margin='5px';b.addEventListener('click',()=>{docId=d.id;$('#doc-title').value=d.title;$('#doc-body').value=d.content;status('#doc-status','已打开文档。编辑后点击保存。')});box.append(b);
  }
}
async function refreshHistory(){
  const j=await api('/api/trading/state'),box=$('#history-list');box.replaceChildren();
  const ss=[...j.sessions].reverse();
  if(!ss.length)box.append(el('p','尚无已采用会话'));
  for(const s of ss){
    const b=el('button',s.date+' · '+s.node+' · '+s.topic+'（'+s.messages.length+'条）','alt');
    b.style.margin='5px';b.addEventListener('click',()=>$('#history-view').textContent=JSON.stringify(s,null,2));box.append(b);
  }
}
async function launch(){
  try{
    const j=await api('/api/trading/people');
    people=j.people;if(people.length!==65)throw Error('65人正式档案未完整加载');
    paintSelector();paintRoster();
  }catch(e){status('#make-status','读取人物资料失败：'+e.message);status('#peoplelist','无法加载65人正式资料，请检查仓库文件。');}
}
for(let i=1;i<=16;i++){const o=el('option','RO-'+String(i).padStart(2,'0'));o.value=o.textContent;$('#node').append(o)}
try{$('#date').value=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Bucharest',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())}catch(e){}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));
  document.querySelectorAll('.section').forEach(x=>x.classList.toggle('active',x.id==='tab-'+b.dataset.tab));
  if(b.dataset.tab==='docs')refreshDocs().catch(e=>status('#doc-status',e.message));
  if(b.dataset.tab==='history')refreshHistory().catch(e=>status('#history-view',e.message));
}));
$('#find').addEventListener('input',paintSelector);$('#people-search').addEventListener('input',paintRoster);
$('#clear').onclick=()=>{selected.clear();paintSelector()};
$('#make').onclick=async()=>{
  verified=false;draftId=null;$('#make').disabled=true;status('#make-status','正在核对65人资料与场次…');
  try{
    const p=await api('/api/trading/prompt',{date:$('#date').value,node:$('#node').value,topic:$('#topic').value,
      source_kind:$('#source_kind').value,source_text:$('#source_text').value,selected_ids:[...selected]});
    draftId=p.prompt.draft_id;$('#prompt').value=JSON.stringify(p.prompt,null,2);
    status('#make-status','提示词已生成，人物：'+p.prompt.selected_characters.length+'，草稿ID：'+draftId.slice(0,8));
  }catch(e){status('#make-status','生成失败：'+e.message)}
  finally{$('#make').disabled=false}
};
$('#copy').onclick=async()=>{if(!$('#prompt').value)return;try{await navigator.clipboard.writeText($('#prompt').value);status('#make-status','完整提示词已复制')}catch(e){$('#prompt').focus();$('#prompt').select();status('#make-status','已选中提示词，请按 Ctrl+C 复制')}};
$('#response').oninput=()=>{verified=false;status('#review-status','内容已修改，需要重新检查')};
$('#check').onclick=async()=>{
  try{
    if(!draftId)throw Error('先生成提示词');
    const raw=JSON.parse($('#response').value),r=await api('/api/trading/validate',{draft_id:draftId,response:raw});
    verified=r.valid;$('#review-output').textContent=JSON.stringify(r,null,2);
    status('#review-status',r.valid?'结构与65人身份校验通过；仍需人工核对自然语言与事实。':'检查未通过：'+r.errors.join('；'));
  }catch(e){verified=false;status('#review-status','检查失败：'+e.message)}
};
$('#adopt').onclick=async()=>{
  if(!draftId||!verified){status('#review-status','先生成提示词并完成草稿检查。');return}
  if(!confirm('确认将这个虚构演练草稿正式采用并写入本地历史？'))return;
  try{
    const data=JSON.parse($('#response').value);
    const r=await api('/api/trading/adopt',{draft_id:draftId,response:data,confirmed:true});
    status('#review-status','已正式保存：'+r.session.id+'，共'+r.session.messages.length+'条。');
    verified=false;draftId=null;
  }catch(e){verified=false;status('#review-status','保存失败：'+e.message)}
};
$('#new-doc').onclick=()=>{docId=null;$('#doc-title').value='';$('#doc-body').value='';status('#doc-status','已新建空白编辑区；尚未保存。')};
$('#save-doc').onclick=async()=>{
  try{const r=await api('/api/trading/docs',{id:docId,title:$('#doc-title').value,content:$('#doc-body').value});
    docId=r.doc.id;status('#doc-status','文档已保存到本机写作目录：'+r.doc.updated_at);await refreshDocs();
  }catch(e){status('#doc-status','保存失败：'+e.message)}
};
$('#refresh-history').onclick=()=>refreshHistory().catch(e=>status('#history-view',e.message));
launch();
if(location.hash==="#tab-people"){
  const peopleTab=document.querySelector('[data-tab="people"]');
  if(peopleTab)peopleTab.click();
}
</script></body></html>'''
