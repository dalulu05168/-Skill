#!/usr/bin/env python3
"""Produce a public, READ-ONLY visual acceptance build from actual P004 templates.

This is not the backend and does not fake news, investment results, approved
sessions, account balances or external messages. No live APIs are available.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from finance_skill_api import PAGE
from chennan_writing import summaries, load_profiles
from chennan_writing_ui import PAGE as WRITING_PAGE
from trading_center_ui import PAGE as TRADING_PAGE
from image_editor_ui import PAGE as IMAGE_PAGE
from workspace_overview import add_overview
from workspace_theme import apply_visual_system
from workspace_layout import wrap_page
from four_module_gateway import render_gateway
from login_ui import render_login
from bvb_v33_restore import restore_news_v33

OUTPUT = ROOT / "build" / "finance-ui-readonly-preview"
BANNER = (
    '<div role="status" class="readonly-preview-banner">'
    '<strong>UI 只读预览</strong><span>新闻审核与人物保存等后端功能未连接，请勿输入私人资料。</span>'
    '</div>'
)
STYLE = """<style>
.readonly-preview-banner { display: flex;align-items:center;gap:9px;flex-wrap:wrap;
 background:#f9fafb;border:1px solid #dce4ec;color:#4d5f73;
 padding:5px 9px;border-radius:8px;font:11px/1.4 system-ui,sans-serif;
 margin:4px 0 8px; }
.readonly-preview-banner strong { white-space:nowrap;color:#385777; }
.readonly-preview-banner span{min-width:0; }
.gate-page>section { display:flex;flex-direction:column;min-height:0;flex:1; }
.gate-page .readonly-preview-banner{position:absolute;right:18px;bottom:12px;max-width:440px;font-size:10px;z-index:2; }
.gate-page{position:relative}
.ws-frame{height:min(calc(100dvh - 18px),calc((100vw - 18px) * 9 / 16))!important;
width:min(calc(100vw - 18px),calc((100dvh - 18px) * 16 / 9),1680px)!important;
max-height:calc(100dvh - 18px);min-height:0!important;margin:0 auto!important;grid-template-rows:54px minmax(0,1fr)!important}
.ws-frame>.app{min-height:0!important;overflow:auto!important;scrollbar-width:none;padding:12px 16px 20px!important}
.ws-frame>.app::-webkit-scrollbar{display:none}
.ws-screen-controls{display:flex;gap:5px}
.ws-screen-controls button{border:1px solid #dce3eb;border-radius:8px;background:#fff;color:#37536d;font-size:11px;font-weight:700;padding:7px 10px;white-space:nowrap}
.ws-screen-controls button:disabled{opacity:.35;cursor:not-allowed}
.ws-screen-controls button:not(:disabled):hover{background:#eff5fa}
html,body{height:100%;overflow:hidden!important}
@media(max-width:700px){.ws-frame{width:100%!important;height:100dvh!important;max-height:none;margin:0!important;grid-template-columns:55px minmax(0,1fr)!important}
.gate-page .readonly-preview-banner{display:none}
}
button[disabled], select[disabled], textarea[disabled], input[disabled] { opacity:.67; cursor: not-allowed; }
.preview-member-card { border:1px solid #e5e9ef; border-radius:12px; padding:12px;
 background:white; margin:4px; font-size:13px; line-height:1.7; }
.preview-member-card b { display:block; color:#24313d; }
.preview-member-card small {display:block; color:#687683;}
@media(max-width:700px) { .readonly-preview-banner { font-size:12px; } }
</style>"""
SCRIPT = """<script>
/* Only client-side navigation/filters. No network operations. */
(function(){
 'use strict';
 const search=document.getElementById('ws-member-search');
 const rows=[...document.querySelectorAll('#ws-members-body tr[data-person]')];
 if(search) search.addEventListener('input', ()=>{
   const q=search.value.trim().toLocaleLowerCase();
   rows.forEach(r=>r.hidden=!!q && !r.dataset.search.includes(q));
 });
 const buttons=[...document.querySelectorAll('.tabs button[data-tab]')];
 for(const btn of buttons){
   btn.disabled=false;
   btn.addEventListener('click',()=>{
     const target=btn.dataset.tab;
     for(const b of buttons)b.classList.toggle('active',b===btn);
     for(const part of document.querySelectorAll('.section[id^="tab-"]')){
       part.classList.toggle('active',part.id==='tab-'+target);
     }
   });
 }
 if(/^#tab-(script|people|docs|history)$/.test(location.hash)) {
   const btn=document.querySelector('.tabs button[data-tab="'+location.hash.slice(5)+'"]');
   if(btn)btn.click();
 }
 const filters=[...document.querySelectorAll('[data-ws-role]')];
 for(const btn of filters){
  btn.disabled=false;
  btn.addEventListener('click',()=>{
   filters.forEach(b=>b.classList.toggle('active',b===btn));
   const target=btn.dataset.wsRole;
   for(const row of rows){
    row.hidden=(target!=='all' && row.dataset.role!==target) ||
      (!!search?.value && !row.dataset.search.includes(search.value.trim().toLocaleLowerCase()));
   }
  });
 }
 // Desktop is a fixed 16:9 viewport: move through overflow content only via
 // explicit screen navigation, never by making the whole page scroll.
 const content=document.querySelector('.ws-frame > .app');
 const topRight=document.querySelector('.ws-top-right');
 if(content && topRight){
   const controls=document.createElement('div');controls.className='ws-screen-controls';
   const previous=document.createElement('button');
   previous.type='button';previous.textContent='上一屏';previous.setAttribute('aria-label','查看上一屏');
   const next=document.createElement('button');
   next.type='button';next.textContent='下一屏';next.setAttribute('aria-label','查看下一屏');
   controls.append(previous,next);topRight.prepend(controls);
   const move=delta=>content.scrollBy({top:delta*content.clientHeight*.84,behavior:'smooth'});
   previous.addEventListener('click',()=>move(-1));
   next.addEventListener('click',()=>move(1));
   const refresh=()=>{
      previous.disabled=content.scrollTop<8;
      next.disabled=content.scrollTop+content.clientHeight>=content.scrollHeight-8;
   };
   content.addEventListener('scroll',refresh);
   window.addEventListener('resize',refresh);
   content.addEventListener('wheel',e=>e.preventDefault(),{passive:false});
   refresh();
 }
})();
</script>"""

def _safe(value):
    return html.escape(str(value if value is not None else "—"), quote=True)

def _compose_skill():
    # Same label logic as the real /skill route: visual-only build.
    return (WRITING_PAGE
        .replace("<title>交易中心 · 65人统一交易与人物工作台</title>",
                 "<title>财经 Skill · 课程、群聊与记忆</title>")
        .replace("交易中心 · 统一交易与人物工作台",
                 "财经 Skill · 课程、群聊与记忆")
        .replace('data-tab="script">脚本撰写', 'data-tab="script">群聊脚本')
        .replace('data-tab="docs">写作文档', 'data-tab="docs">课程资料与文档')
        .replace('data-tab="history">正式会话与记忆',
                 'data-tab="history">正式会话与人物记忆'))

def _roster_rows(people):
    return "".join(
       '<tr data-person="1" data-role="'+_safe(p.get("role"))+'" data-search="'+
       _safe(" ".join(str(p.get(k,"")) for k in ("character_id","name","city","occupation","role")).lower())+'">'
       '<td><b>'+_safe(p["character_id"])+ ' · '+_safe(p["name"])+'</b></td>'
       '<td>'+_safe(p.get("occupation"))+'</td>'
       '<td>'+_safe(p.get("city"))+'</td>'
       '<td>'+_safe(p.get("role"))+'</td>'
       '<td>未知</td><td>预览只读</td></tr>'
       for p in people
    )

def build():
    profiles=load_profiles()
    people=summaries(profiles)
    if len(people)!=65:
        raise RuntimeError("Authoritative roster must contain exactly 65 people")

    pages = {
      "": render_login(preview=True),
      "workspace": render_gateway(),
      "news": wrap_page(apply_visual_system(add_overview(PAGE)), "news"),  # overwritten by authentic restored v3.3
      "news-legacy": wrap_page(apply_visual_system(add_overview(PAGE)), "news"),
      "skill": wrap_page(apply_visual_system(_compose_skill()), "skill"),
      "trading": wrap_page(apply_visual_system(TRADING_PAGE), "trading"),
      "image-editor": IMAGE_PAGE,
      "trade-platform": IMAGE_PAGE,  # compatibility alias
    }
    for route, page in pages.items():
        # Remove all original API-backed JS. Its actions have no corresponding
        # server in a static preview and must not pretend to work.
        if route not in ("image-editor", "trade-platform"):
            page = re.sub(r"<script\b[^>]*>.*?</script>", "", page,
                          flags=re.IGNORECASE|re.DOTALL)
        page=page.replace("</head>", STYLE+"</head>", 1)
        # Disable unsafe/nonworking original action controls but keep
        # navigational links, tabs and person search in the static preview.
        if route not in ("image-editor", "trade-platform"):
            page = re.sub(r"<button(?![^>]*\bdisabled\b)([^>]*)>",
                          r"<button disabled\1>", page, flags=re.IGNORECASE)
            page = re.sub(r'<textarea\b(?![^>]*\bdisabled\b)([^>]*)>',
                          r'<textarea disabled\1>',page,flags=re.IGNORECASE)
            page = re.sub(r'<select\b(?![^>]*\bdisabled\b)([^>]*)>',
                          r'<select disabled\1>',page,flags=re.IGNORECASE)
        page = page.replace('<main class="app">', '<main class="app">'+BANNER, 1)
        if route=="workspace":
            page = page.replace('<header class="gate-header">',
                                '<header class="gate-header">', 1)
            page = page.replace('<section aria-labelledby="gateway-title">',
                                BANNER+'<section aria-labelledby="gateway-title">', 1)
        page = page.replace('<div class="app">', '<div class="app">'+BANNER, 1)
        if route=="news":
            page=re.sub(r'<tbody id="ws-members-body">.*?</tbody>',
                        '<tbody id="ws-members-body">'+_roster_rows(people)+'</tbody>',
                        page, flags=re.DOTALL)
            page=page.replace('id="ws-people-count">—', 'id="ws-people-count">65', 1)
            page=page.replace('正在读取65份正式档案…', '65份正式档案已随预览构建完成')
            page=page.replace('本地内部审核 · 无自动发布', '线上只读界面预览', 1)
        if route=="skill":
            cards="".join('<article class="preview-member-card"><b>'+
                          _safe(p["character_id"])+ ' · '+_safe(p["name"])+
                          '</b><small>'+_safe(p.get("occupation"))+
                          ' · '+_safe(p.get("role"))+
                          ' · '+_safe(p.get("city"))+'</small></article>'
                          for p in people)
            page=page.replace('id="peoplelist"><span class="muted">正在读取正式人物库…</span>',
                              'id="peoplelist">'+cards,1)
            page=page.replace('id="roster" class="layout"></div>',
                              'id="roster" class="layout">'+cards+'</div>',1)
            page=page.replace('id="history-list"></div>',
                              'id="history-list"><p>只读界面预览没有云端正式会话；不会伪造历史记录。</p></div>',1)
        if route != "":
            page = page.replace('href="/"', 'href="/workspace/"')
        page = page.replace('href="/news"', 'href="/news/"')
        page = page.replace('href="/skill"', 'href="/skill/"')
        page = page.replace('href="/trading"', 'href="/trading/"')
        page = page.replace('href="/image-editor"', 'href="/image-editor/"')
        page = page.replace('href="/trade-platform"', 'href="/image-editor/"')
        page = page.replace('href="/skill#tab-people"', 'href="/skill/#tab-people"')
        page = page.replace('href="/trading#tc-profile"', 'href="/trading/#tc-profile"')
        if route not in ("image-editor", "trade-platform"):
            page = page.replace("</body>", SCRIPT+"</body>",1)
        destination = OUTPUT / route / "index.html" if route else OUTPUT / "index.html"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(page,encoding="utf-8")
    restored_hashes = restore_news_v33(OUTPUT / "news")
    (OUTPUT/"preview-manifest.json").write_text(
      json.dumps({"project":"P004","kind":"UI-READONLY-PREVIEW",
                  "source":"canonical -Skill frontend templates",
                  "persona_count":65,"backend_connected":False,
                   "module_one":{"name":"BVB News Desk 中文 v3.3",
                       "status":"original_frontend_restored",
                       "source_hashes":restored_hashes,
                       "local_editor_enabled":True,
                       "cloud_collectors_connected":False},
                  "news_verified":False,"persistent_memory":False,
                  "publication_enabled":False},ensure_ascii=False,indent=2),
      encoding="utf-8")
    print(f"Built {len(pages)} pages; restored authentic BVB v3.3 at /news/; " 
          f"cloud collectors OFF; {len(people)} personas")

if __name__ == "__main__":
    build()
