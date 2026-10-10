"""Trading-only UI. Editorial scripts, courses, sessions and memory are served by /skill.

Reuse the existing 65-person simulation markup and validated APIs without copying
or changing member histories or bringing back the legacy 70/72-person data.
"""
from html import escape
from chennan_writing_ui import PAGE as EDITORIAL_PAGE
from trading_65_ui import SECTION, SCRIPT

BASE_CSS = EDITORIAL_PAGE.split("<style>", 1)[1].split("</style>", 1)[0]
SIM_CSS = SECTION.split("<style>", 1)[1].split("</style>", 1)[0]
SIM_BODY = SECTION.split("</style>", 1)[1].replace(
    '<div class="section" id="tab-sim">',
    '<div class="section active" id="tab-sim">', 1,
)

PAGE = (
    '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>交易中心 · 65人模拟买卖与持仓</title><style>'
    + BASE_CSS + "\n" + SIM_CSS + """
:root{color-scheme:light}
body{background:#fff!important;color:#20242a}
.tc-note{margin:14px 0;padding:14px 16px;border:1px solid #e5e8ed;border-radius:12px;background:#fff;color:#535d67}
.tc-tools{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:13px 0}
.tc-tools a{color:#29323c;border:1px solid #e1e5ea;background:#fff;border-radius:10px;padding:9px 13px;font-weight:700}
.tc-profile{margin-top:18px}
.tc-profile select{max-width:460px}
.tc-profile pre{white-space:pre-wrap;overflow:auto;max-height:420px;font-size:12px}
@media(hover:hover){.tc-tools a:hover{background:#f7f8fa;border-color:#c7ced7}}
""" + '</style></head><body><main class="app">'
    + """
<div class="top"><div><div class="brand">NUVEXA <span>· 交易中心</span></div>
<div class="sub">正式65人数据源 · 模拟股票买卖与持仓</div></div>
<nav aria-label="主模块"><a href="/">新闻推送</a><a class="active" href="/trading" aria-current="page">交易中心</a>
<a href="/skill">财经 Skill</a><a href="/trade-platform">图片编辑器</a></nav></div>
<h1>交易中心 · 模拟买卖与持仓</h1>
<p>65名成员的身份资料直接读取正式 v4.1 人物库。此页面只负责模拟交易资格、股票计划、买入、持仓、卖出与对应的交易事实记录。</p>
<div class="tc-note">课程资料、群聊脚本、正式会话与人物记忆统一在
<a href="/skill">财经 Skill</a> 处理；交易中心不再显示这些栏目。
所有交易和金额均为明确标注的内部模拟，不是证券实盘记录。</div>
<div class="tabs"><button type="button" class="active" data-tab="sim">模拟买卖与持仓</button>
<a href="#tc-profile" class="btnlink">65人完整档案</a><a href="/skill" class="btnlink">前往财经 Skill</a></div>
"""
    + SIM_BODY
    + """
<section class="card tc-profile" id="tc-profile">
<h2>65人完整人物资料（只读）</h2>
<p class="muted">查看人物身份、性格、说话方式、职业与投资习惯；交易资格和模拟资金单独设定，不改动原始人设。</p>
<label for="tc-profile-select">选择查看人物</label>
<select id="tc-profile-select"><option value="">正在载入成员…</option></select>
<pre id="tc-profile-detail">选择人物后显示其完整档案。这里不修改角色记忆。</pre>
</section>
"""
    + SCRIPT
    + """<script>
(function(){
'use strict';
const start=document.querySelector('[data-tab="sim"]');
if(start) start.click();
const select=document.getElementById('tc-profile-select');
const output=document.getElementById('tc-profile-detail');
async function requestJson(path){
 const r=await fetch(path,{credentials:'same-origin'});
 const j=await r.json();
 if(!r.ok)throw new Error(j.error||'HTTP '+r.status);
 return j;
}
requestJson('/api/trading/people').then(j=>{
 if(j.people.length!==65)throw Error('正式65人数据源不完整');
 select.replaceChildren(new Option('选择一位成员',''));
 j.people.forEach(p=>select.add(new Option(p.character_id+' · '+p.name+' · '+p.occupation,p.character_id)));
}).catch(e=>{output.textContent='读取人物数据失败：'+e.message});
select.addEventListener('change',async()=>{
 if(!select.value){output.textContent='选择人物后显示完整档案';return}
 output.textContent='正在读取已校验的人物档案…';
 try {
  const j=await requestJson('/api/trading/profile?character_id='+encodeURIComponent(select.value));
  output.textContent=JSON.stringify(j.profile,null,2);
 }catch(e){output.textContent='读取失败：'+e.message}
});
})();
</script></main></body></html>"""
)
