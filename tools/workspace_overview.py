"""Real-data overview for the unified 65-person finance workspace.

Read-only dashboard. All KPI counts come from validated official roster or
persisted local review/approved sessions. No fake financial prices or activity.
"""
import json
from pathlib import Path

from chennan_writing import load_profiles, read_state

OVERVIEW = r'''
<section class="ws-overview" id="ws-overview" aria-label="工作台概览">
  <div class="ws-pageheading">
    <div><div class="ws-eyebrow">FINANCE OPERATIONS · UNIFIED WORKSPACE</div>
      <h1>统一交易工作台</h1>
      <p>新闻推送、交易中心与65人虚构成员资料在同一工作台管理；所有显示数字均来自本机已保存记录。</p>
    </div><div class="ws-readonly">● 内部工作台 · 非实盘</div>
  </div>
  <div class="ws-kpis">
    <article class="ws-kpi" aria-label="上次审核候审新闻数量"><div class="ws-kpi-top"><span class="ws-kpi-icon teal">▤</span><div><strong>新闻候审</strong><small>上次审核结果</small></div></div><div class="ws-kpi-num" id="ws-news-count">—</div><div class="ws-kpi-note" id="ws-news-note">尚无审核数据</div></article>
    <article class="ws-kpi" aria-label="已正式采用会话数量"><div class="ws-kpi-top"><span class="ws-kpi-icon blue">▥</span><div><strong>交易中心</strong><small>正式采用的模拟会话</small></div></div><div class="ws-kpi-num" id="ws-trading-count">—</div><div class="ws-kpi-note" id="ws-trading-note">正在读取本机归档</div></article>
    <article class="ws-kpi" aria-label="正式人物档案总数量"><div class="ws-kpi-top"><span class="ws-kpi-icon purple">♧</span><div><strong>65人成员</strong><small>唯一正式档案库</small></div></div><div class="ws-kpi-num" id="ws-people-count">—</div><div class="ws-kpi-note" id="ws-people-note">正在进行身份交叉校验</div></article>
    <article class="ws-kpi" aria-label="审核闸门状态"><div class="ws-kpi-top"><span class="ws-kpi-icon orange">✓</span><div><strong>审核与发布</strong><small>仅显示已知审批状态</small></div></div><div class="ws-kpi-num" id="ws-review-count">—</div><div class="ws-kpi-note" id="ws-review-note">无自动外部发布</div></article>
  </div>
  <nav class="ws-tabs" aria-label="业务模块标签">
    <a class="active" href="#ws-overview" aria-current="page">概览</a>
    <a href="#news-process">新闻推送</a>
    <a href="/trading">交易中心</a>
    <a href="/trading#tc-profile">65人人物档案</a>
    <a href="/trade-platform">外部交易平台</a>
  </nav>
  <div class="ws-controls">
    <div class="ws-filter-group" role="group" aria-label="人物类型筛选">
      <button type="button" class="ws-filter active" data-ws-role="all">全部成员 (65)</button>
      <button type="button" class="ws-filter" data-ws-role="老女">老女</button>
      <button type="button" class="ws-filter" data-ws-role="新女">新女</button>
      <button type="button" class="ws-filter" data-ws-role="老男">老男</button>
      <button type="button" class="ws-filter" data-ws-role="新男">新男</button>
    </div>
    <label class="ws-search-label">搜索人物 <input type="search" id="ws-member-search" placeholder="编号、姓名、城市、职业"></label>
  </div>
  <div class="ws-table-panel">
    <div class="ws-table-scroll">
      <table class="ws-table"><thead><tr><th>正式成员</th><th>职业</th><th>所在地</th><th>人物分类</th><th>在线状态</th><th>资料</th></tr></thead>
      <tbody id="ws-members-body"><tr><td colspan="6">正在读取65份正式档案…</td></tr></tbody></table>
    </div>
    <div class="ws-table-foot"><span id="ws-members-note">只读取本机权威人物库；并非WhatsApp实时在线监控。</span>
      <button type="button" id="ws-expand" class="ws-secondary-button" hidden>查看全部65人</button>
    </div>
  </div>
  <div class="ws-clarification">“在线状态”在没有真实接口时一律显示未知；新闻候审数字若存在，仅代表上次已保存的内部审核包，不代表实时行情、真实成员、真实交易或已完成发布。</div>
</section>
<section class="ws-news-area" id="news-process" aria-label="新闻推送与AI审核">
<div class="ws-section-label">NEWS PUSH & EDITORIAL REVIEW <span>· 新闻推送与审核工具</span></div>
</section>
<dialog id="ws-profile-dialog" class="ws-dialog" aria-labelledby="ws-dialog-title">
  <form method="dialog"><button class="ws-dialog-close" aria-label="关闭档案">×</button></form>
  <h2 id="ws-dialog-title">正式人物档案</h2>
  <pre id="ws-profile-data">正在读取…</pre>
</dialog>
'''

SCRIPT = r'''
<script>
(function(){
"use strict";
const section=document.getElementById("ws-overview");if(!section)return;
const val=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
const tbody=document.getElementById("ws-members-body");
const search=document.getElementById("ws-member-search");
const expand=document.getElementById("ws-expand");
const dialog=document.getElementById("ws-profile-dialog");
let members=[],filter="all",showAll=false;
async function load(url){const r=await fetch(url,{credentials:"same-origin"}),j=await r.json();if(!r.ok)throw Error(j.error||"服务暂不可用");return j;}
function cell(tr,content){const td=document.createElement("td");td.textContent=content;tr.append(td);return td}
function filtered(){const q=search.value.trim().toLocaleLowerCase();return members.filter(p=>
  (filter==="all"||p.role===filter)&&
  [p.character_id,p.name,p.occupation,p.city,p.role].join(" ").toLocaleLowerCase().includes(q)
)}
function render(){
  const all=filtered(),visible=showAll?all:all.slice(0,8);tbody.replaceChildren();
  for(const p of visible){
    const row=document.createElement("tr");
    const td=document.createElement("td");
    const entry=document.createElement("div");entry.className="ws-person-cell";
    const badge=document.createElement("span");badge.className="ws-person-avatar";
    badge.textContent=p.character_id;
    const name=document.createElement("div");name.className="ws-person-name";name.textContent=p.name;
    const subtitle=document.createElement("small");subtitle.textContent="#"+p.character_id+" · 虚构教育角色";
    const nameBlock=document.createElement("div");nameBlock.append(name,subtitle);
    entry.append(badge,nameBlock);td.append(entry);row.append(td);
    cell(row,p.occupation||"—");cell(row,p.city||"—");
    const classification=cell(row,p.role);classification.className="ws-classification";
    const status=cell(row,"未知");status.className="ws-unknown";
    const action=document.createElement("td"),button=document.createElement("button");
    button.type="button";button.className="ws-row-action";button.textContent="查看档案";
    button.addEventListener("click",async()=>{
      val("ws-dialog-title",p.character_id+" · "+p.name+" / 正式档案");
      val("ws-profile-data","正在读取…");dialog.showModal();
      try{const detail=await load("/api/trading/profile?character_id="+encodeURIComponent(p.character_id));
        val("ws-profile-data",JSON.stringify(detail.profile,null,2));
      }catch(e){val("ws-profile-data","无法读取档案："+e.message)}
    });action.append(button);row.append(action);tbody.append(row);
  }
  if(!visible.length){const row=document.createElement("tr");cell(row,"没有匹配成员").colSpan=6;tbody.append(row)}
  val("ws-members-note","显示 "+visible.length+" / "+all.length+" 名筛选结果 · 正式人物库总数65 · 在线状态未知");
  expand.hidden=showAll||all.length<=8;
}
document.querySelectorAll("[data-ws-role]").forEach(button=>{
  button.addEventListener("click",()=>{
    document.querySelectorAll("[data-ws-role]").forEach(b=>b.classList.remove("active"));
    button.classList.add("active");filter=button.dataset.wsRole;showAll=false;render();
  });
});
search.addEventListener("input",()=>{showAll=false;render()});
expand.addEventListener("click",()=>{showAll=true;render()});
document.querySelector(".ws-dialog-close")?.addEventListener("click",()=>dialog.close());
const qs=new URLSearchParams(location.search).get("member");
if(qs)search.value=qs.slice(0,80);
Promise.all([load("/api/trading/people"),load("/api/dashboard/summary")])
.then(([roster,summary])=>{
  if(roster.count!==65||roster.people?.length!==65||summary.roster_count!==65)throw Error("65人成员数量校验失败");
  members=roster.people;render();
  val("ws-people-count","65 / 65");val("ws-people-note","65份正式人物身份已校验");
  val("ws-trading-count",String(summary.adopted_sessions));
  val("ws-trading-note","另有 "+summary.documents+" 份写作文档");
  if(summary.last_news_review){
    const report=summary.last_news_review;
    val("ws-news-count",report.pending_count===null?"—":String(report.pending_count));
    val("ws-news-note","上次审核包 · "+(report.generated_at||"时间未知"));
    val("ws-review-count",report.status||"—");
    val("ws-review-note","仍须人工审核，无自动推送");
  }else{
    val("ws-news-count","—");val("ws-news-note","未找到本机审核记录");
    val("ws-review-count","未运行");val("ws-review-note","无自动外部发布");
  }
}).catch(e=>{
  tbody.replaceChildren();const row=document.createElement("tr");cell(row,"人物/审核数据获取失败："+e.message).colSpan=6;tbody.append(row);
  val("ws-people-note","加载失败，不显示演示数据");
  val("ws-trading-note","本机状态尚不可用");
});
})();
</script>
'''

def dashboard_summary(data_dir):
    """Do not fabricate metrics on empty/malformed data directory."""
    roster = load_profiles() # validates all 65 official profiles
    data_dir=Path(data_dir)
    state = read_state(data_dir / "chennan-writing-65.json")
    result = {"roster_count":len(roster),"roster_source":"finance-director-65-v4.1",
              "adopted_sessions":len(state["sessions"]),"documents":len(state["docs"]),
              "last_news_review":None}
    path=data_dir / "latest-internal-review.json"
    if path.exists():
        packet=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(packet,dict) or packet.get("runner")!="unified-finance-skill-hub":
            raise ValueError("Stored news packet is invalid")
        news=packet.get("news",{});review=packet.get("review",{})
        pending=news.get("pending_count")
        if not isinstance(pending,int) or isinstance(pending,bool) or pending<0:
            raise ValueError("Invalid pending news count")
        result["last_news_review"]={
            "pending_count":pending,"generated_at":packet.get("generated_at"),
            "status":review.get("status") if review.get("status") in ("BLOCKED","NEEDS_REVIEW") else "UNKNOWN"
        }
    return result

def add_overview(page):
    anchor='<nav class="row" aria-label="工作台模块">'
    pos=page.find(anchor)
    if pos<0:
        raise ValueError("Unified finance navigation not found")
    closing=page.find("</nav>",pos)
    if closing<0:
        raise ValueError("Finance navigation is malformed")
    page=page[:closing+6]+"\n"+OVERVIEW+page[closing+6:]
    # root page retains the same news controls, now below the overview card/table.
    return page.replace("</body>",SCRIPT+"</body>",1)
