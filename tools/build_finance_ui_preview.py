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
from external_trade_ui import PAGE as TRADE_PAGE
from workspace_overview import add_overview
from workspace_theme import apply_visual_system
from workspace_layout import wrap_page

OUTPUT = ROOT / "build" / "finance-ui-readonly-preview"
BANNER = (
    '<section role="status" class="readonly-preview-banner">'
    '<strong>界面验收预览 · 非正式业务后台</strong>'
    '<span>本预览直接根据 P004 页面源码构建，仅展示布局及65位既有人物的非敏感摘要。'
    '新闻审核、角色记忆保存、AI生成、交易记录与群消息操作未在此站点连接。'
    '请勿输入账号、正文或私人资料。</span></section>'
)
STYLE = """<style>
.readonly-preview-banner { margin: 10px 0 18px; display: flex; gap: 12px;
 flex-wrap: wrap; background: #fff9eb; border: 1px solid #e8d5ae;
 color: #654913; padding: 13px 17px; border-radius: 12px;
 font: 13px/1.65 system-ui, sans-serif; }
.readonly-preview-banner strong { white-space:nowrap; }
.readonly-preview-banner span { flex:1; min-width:240px; }
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
      "": wrap_page(apply_visual_system(add_overview(PAGE)), "news"),
      "skill": wrap_page(apply_visual_system(_compose_skill()), "skill"),
      "trading": wrap_page(apply_visual_system(TRADING_PAGE), "trading"),
      "trade-platform": wrap_page(apply_visual_system(TRADE_PAGE), "external"),
    }
    for route, page in pages.items():
        # Remove all original API-backed JS. Its actions have no corresponding
        # server in a static preview and must not pretend to work.
        page = re.sub(r"<script\b[^>]*>.*?</script>", "", page,
                      flags=re.IGNORECASE|re.DOTALL)
        page=page.replace("</head>", STYLE+"</head>", 1)
        # Disable unsafe/nonworking original action controls but keep
        # navigational links, tabs and person search in the static preview.
        page = re.sub(r"<button(?![^>]*\bdisabled\b)([^>]*)>",
                      r"<button disabled\1>", page, flags=re.IGNORECASE)
        page = re.sub(r'<textarea\b(?![^>]*\bdisabled\b)([^>]*)>',
                      r'<textarea disabled\1>',page,flags=re.IGNORECASE)
        page = re.sub(r'<select\b(?![^>]*\bdisabled\b)([^>]*)>',
                      r'<select disabled\1>',page,flags=re.IGNORECASE)
        page = page.replace('<main class="app">', '<main class="app">'+BANNER, 1)
        page = page.replace('<div class="app">', '<div class="app">'+BANNER, 1)
        if route=="":
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
        page = page.replace('href="/skill"', 'href="/skill/"')
        page = page.replace('href="/trading"', 'href="/trading/"')
        page = page.replace('href="/trade-platform"', 'href="/trade-platform/"')
        page = page.replace('href="/skill#tab-people"', 'href="/skill/#tab-people"')
        page = page.replace('href="/trading#tc-profile"', 'href="/trading/#tc-profile"')
        page = page.replace("</body>", SCRIPT+"</body>",1)
        destination = OUTPUT / route / "index.html" if route else OUTPUT / "index.html"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(page,encoding="utf-8")
    (OUTPUT/"preview-manifest.json").write_text(
      json.dumps({"project":"P004","kind":"UI-READONLY-PREVIEW",
                  "source":"canonical -Skill frontend templates",
                  "persona_count":65,"backend_connected":False,
                  "news_verified":False,"persistent_memory":False,
                  "publication_enabled":False},ensure_ascii=False,indent=2),
      encoding="utf-8")
    print(f"Built {len(pages)} safe read-only pages from current P004 source, {len(people)} personas")

if __name__ == "__main__":
    build()
