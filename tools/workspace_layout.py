"""Responsive app-wide chrome matching the selected light fintech reference.

Keeps original route content/buttons, injects real navigation, and adds no
external fonts, remote images, fake metrics or decorative nonfunctional actions.
"""
from html import escape

ICONS = {
    "overview": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "news": '<rect x="5" y="4" width="12" height="15" rx="1.5"/><path d="M9 8h4M9 12h4M9 16h4M17 8h2v13H8"/>',
    "trading": '<path d="M4 20V12h4v8M10 20V5h4v15M16 20v-9h4v9"/>',
    "people": '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 5v1"/>',
    "external": '<path d="M14 4h6v6M10 14 20 4M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
    "review": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
}

def icon(name):
    return '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'+ICONS[name]+'</svg>'

SHELL_CSS = r'''
/* Shared design system: approved white/gray + soft teal fintech screenshot */
:root{
 --ws-teal:#3b4652;--ws-teal-pale:#f3f5f7;--ws-ink:#1d2329;--ws-dim:#77818a;
 --ws-border:#e6e9ed;--ws-line:#eef0f2;--ws-shadow:0 12px 36px #1118270c;
 --ui-gold:#3b4652;--ui-gold-soft:#f3f5f7;
}
html{scroll-behavior:smooth}
body{background:#ffffff;color:var(--ws-ink);font-family:Inter,"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif}
.ws-frame{display:grid;grid-template-columns:76px minmax(0,1fr);grid-template-rows:66px minmax(0,1fr);
 min-height:min(900px,calc(100vh - 60px));width:min(1510px,calc(100% - 58px));margin:30px auto;
 background:#fff;border:1px solid #e7edec;border-radius:8px;box-shadow:var(--ws-shadow);overflow:clip}
.ws-rail{grid-area:1/1/3/2;border-right:1px solid var(--ws-border);background:linear-gradient(180deg,#fff,#fcfcfd);padding:16px 0;display:flex;flex-direction:column;align-items:stretch}
.ws-mark{display:block;text-align:center;text-decoration:none;font-size:23px;font-weight:900;letter-spacing:-.1em;color:#13262a;margin:0 0 30px;line-height:32px}
.ws-mark i{color:var(--ws-teal);font-style:normal}
.ws-rail-links{display:flex;flex-direction:column;gap:7px}
.ws-rail-link{position:relative;display:flex;align-items:center;justify-content:center;flex-direction:column;
 gap:5px;padding:11px 2px;min-height:66px;text-decoration:none!important;color:#626b73!important;
 font-size:10px;font-weight:600;line-height:1.3;transition:background .16s ease,color .16s ease}
.ws-rail-link svg{flex-shrink:0}
.ws-rail-link:hover{background:#f4f8f8;color:#1e5554!important}
.ws-rail-link.active{color:#1c4141!important;background:#f4faf9}
.ws-rail-link.active::before{content:"";position:absolute;width:3px;left:0;top:0;bottom:0;background:var(--ws-teal)}
.ws-top{grid-area:1/2/2/3;border-bottom:1px solid var(--ws-border);background:#fff;
 display:flex;align-items:center;justify-content:space-between;gap:18px;padding:10px 23px}
.ws-top-search{min-width:250px;width:min(430px,70%);display:flex;align-items:center;gap:11px;
 height:42px;padding:0 12px;background:#fff;border:1px solid #e5e8eb;border-radius:9px;color:#8a949b}
.ws-top-search input{width:100%;flex:1;font-size:13px;color:#37414a;border:0;padding:2px;min-width:0;height:32px;min-height:32px;outline:0;background:transparent}
.ws-top-search input:focus-visible{outline:0;border:0}
.ws-top-search button{border:0;background:transparent;color:#68737d;padding:6px;cursor:pointer;width:38px;min-width:38px;height:38px;min-height:38px;display:grid;place-items:center;font-size:16px}
.ws-top-right{display:flex;gap:11px;align-items:center}
.ws-top-badge{font-size:11px;color:#68757a;border:1px solid #e5e8eb;border-radius:7px;padding:6px 9px;white-space:nowrap}
.ws-user{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;background:#e7f7f4;border:1px solid #d0e9e4;color:#18827c;font-size:13px;font-weight:850}
.ws-frame > .app{grid-area:2/2/3/3;max-width:none;width:100%;min-height:0;margin:0;
 padding:21px clamp(16px,2vw,29px) 40px;background:#fff;overflow:visible}
.ws-frame > .app > .top,.ws-frame > .app > nav[aria-label="工作台模块"]{display:none!important}
.ws-frame > .app > .top + nav,.ws-frame > .app > .top + .nav{display:none!important}
.ws-frame > .app .logo span,.ws-frame > .app .brand span{color:var(--ws-teal)!important}
.ws-frame > .app h1{font-size:clamp(23px,2.3vw,31px);margin:24px 0 7px;line-height:1.34}
.ws-frame > .app h2{font-size:17px}
.ws-frame > .app .card,.ws-frame > .app .panel{border:1px solid var(--ws-border);border-radius:12px;
 box-shadow:0 2px 10px #28374606}
.ws-frame > .app .btn,.ws-frame > .app button:not(.ws-filter):not(.ws-row-action):not(.ws-secondary-button){border-radius:9px}
.ws-frame > .app .btn.alt,.ws-frame > .app button.alt{background:#ecf7f5;color:#0a7771}
.ws-frame > .app .status{border-left-color:var(--ws-teal)}
.ws-frame > .app input:focus-visible,.ws-frame > .app textarea:focus-visible,
.ws-frame > .app select:focus-visible{outline:2px solid #0a9890;outline-offset:1px}
.ws-overview{padding:0;margin:0}
.ws-pageheading{display:flex;align-items:center;justify-content:space-between;gap:16px}
.ws-pageheading h1{font-size:clamp(26px,2.4vw,33px)!important;font-weight:790;margin:5px 0 4px!important}
.ws-pageheading p{font-size:12px;color:#858b91;margin:0;line-height:1.65}
.ws-eyebrow{color:#0e9287;font-weight:750;font-size:10px;letter-spacing:.1em}
.ws-readonly{background:#f5f9f8;color:#197f76;border:1px solid #e3f2ef;border-radius:50px;
 white-space:nowrap;padding:8px 12px;font-size:11px;font-weight:700}
.ws-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:19px 0 23px}
.ws-kpi{border:1px solid #e7eaed;border-radius:12px;padding:15px 16px 13px;background:#fff;min-width:0}
.ws-kpi-top{display:flex;gap:11px;align-items:center}
.ws-kpi-top strong{font-size:13px;font-weight:790;display:block}
.ws-kpi-top small{font-size:11px;color:#999fa6;display:block;margin-top:0}
.ws-kpi-icon{width:33px;height:33px;border-radius:50%;display:grid;place-items:center;color:#fff;font-size:19px;font-weight:700}
.ws-kpi-icon.teal{background:linear-gradient(135deg,#22b9a8,#0d8e87)}
.ws-kpi-icon.blue{background:linear-gradient(135deg,#34a9ff,#2473d1)}
.ws-kpi-icon.purple{background:linear-gradient(135deg,#a891f1,#8155d9)}
.ws-kpi-icon.orange{background:linear-gradient(135deg,#ffc16a,#f58a35)}
.ws-kpi-num{font-size:25px;font-weight:790;color:#1b2026;line-height:1.25;margin:11px 0 2px;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ws-kpi-note{font-size:11px;color:#7d858c;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ws-tabs{display:flex;gap:26px;flex-wrap:wrap;border-bottom:1px solid #e5e9e9;padding:0;margin:0 0 13px}
.ws-tabs a{font-size:12px;font-weight:650;text-decoration:none;color:#90969e;padding:12px 0 11px;position:relative}
.ws-tabs a.active{color:var(--ws-teal)}
.ws-tabs a.active::after{content:"";position:absolute;height:2px;bottom:-1px;left:0;right:0;background:var(--ws-teal)}
.ws-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:14px 0 8px}
.ws-filter-group{display:flex;flex-wrap:wrap;gap:7px}
.ws-filter{border:1px solid #e5e8ea!important;border-radius:7px!important;font-size:11px!important;
 background:#fff!important;color:#747c83!important;padding:7px 11px!important;cursor:pointer;min-height:32px!important}
.ws-filter.active{color:var(--ws-teal)!important;border-color:#19a5a1!important;background:#effaf9!important}
.ws-search-label{display:flex;align-items:center;gap:9px;margin:0;font-size:11px;white-space:nowrap;color:#778187;font-weight:600}
.ws-search-label input{height:35px;min-height:35px;width:220px;font-size:12px;margin:0;padding:6px 9px}
.ws-table-panel{border:0;background:#fff;min-width:0}
.ws-table-scroll{width:100%;overflow:auto}
.ws-table{border-collapse:collapse;table-layout:auto;width:100%;font-size:12px;text-align:left}
.ws-table th{color:#68717a;font-size:11px;font-weight:700;padding:12px 12px 13px;border-bottom:1px solid #e7e9ed;white-space:nowrap}
.ws-table td{border-bottom:1px solid #f0f1f3;padding:10px 12px;color:#566069;vertical-align:middle;height:53px}
.ws-table td:first-child{min-width:175px}
.ws-person-cell{display:flex;align-items:center;gap:10px}
.ws-person-avatar{flex:none;border-radius:50%;width:31px;height:31px;background:#e9f4fc;
 color:#246aa1;font-weight:750;display:grid;place-items:center;font-size:11px}
.ws-person-name{font-weight:750;color:#28313a;font-size:12px}
.ws-person-cell small{display:block;font-size:10px;color:#a2a7ad}
.ws-classification{color:#7865a8!important}
.ws-unknown{color:#7d858c!important}
.ws-unknown::before{content:"●";font-size:9px;color:#bdc3c7;margin-right:7px}
.ws-row-action{border:1px solid #dae9e7;border-radius:7px;background:#eff7f5;color:#117a73;padding:7px 10px;
 font-size:11px;cursor:pointer;white-space:nowrap}
.ws-row-action:hover{background:#dff2ed}
.ws-table-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 12px;color:#9198a0;font-size:11px}
.ws-secondary-button{border:1px solid #dde9e7;border-radius:7px;background:#fff;color:#12756d;padding:7px 10px;cursor:pointer;font-size:11px}
.ws-clarification{border-top:1px solid #eef1f0;margin-top:8px;padding:12px 2px;color:#a0a6a9;font-size:10.5px}
.ws-news-area{margin-top:29px;padding:13px 0;border-top:1px solid #e5e8ec}
.ws-section-label{font-size:11px;letter-spacing:.08em;font-weight:750;color:#008f88}
.ws-section-label span{letter-spacing:normal;font-weight:600;color:#7a858d}
.ws-dialog{border:1px solid #dce7e5;box-shadow:0 20px 70px #121f2430;width:min(790px,94vw);max-height:80vh;border-radius:13px;padding:22px}
.ws-dialog::backdrop{background:#23353577}
.ws-dialog-close{float:right;border:0;background:#edf4f3;color:#2a5c58;cursor:pointer;font-size:20px}
.ws-dialog pre{font-size:11px;max-height:60vh;overflow:auto;background:#f8fbfa;padding:13px;white-space:pre-wrap}
.ws-frame .note,.ws-frame .warn{border-radius:10px}
@media (max-width:1080px){.ws-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.ws-rail{font-size:10px}}
@media (max-width:760px){
.ws-frame{width:100%;margin:0;min-height:100vh;border-radius:0;grid-template-columns:56px minmax(0,1fr);grid-template-rows:62px auto}
.ws-rail-link{min-height:59px;font-size:9px}.ws-mark{font-size:19px;margin-bottom:15px}
.ws-top{padding:9px 12px}.ws-top-search{width:100%;min-width:0}.ws-top-badge{display:none}
.ws-frame>.app{padding:16px 11px 27px}
.ws-readonly{display:none}
.ws-kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.ws-kpi{padding:12px}
.ws-kpi-top{gap:7px}.ws-kpi-icon{width:29px;height:29px}.ws-kpi-top strong{font-size:12px}
.ws-kpi-top small{font-size:10px}.ws-kpi-num{font-size:21px}
.ws-controls{align-items:flex-start;flex-direction:column}.ws-search-label,.ws-search-label input{width:100%}
.ws-tabs{gap:14px}.ws-tabs a{font-size:11px}
}

/* Consistent white UI across news, trade, skill and external modules. */
.ws-frame{background:#fff;border-color:#e6e9ed;box-shadow:0 12px 36px #1118270c}
.ws-frame .ws-rail,.ws-frame .ws-top,.ws-frame>.app{background:#fff!important}
.ws-frame .ws-rail-link:hover,.ws-frame .ws-rail-link.active{background:#f5f6f8;color:#27313d!important}
.ws-frame .ws-kpi,.ws-frame>.app .card,.ws-frame>.app .panel,.ws-frame .sim-counter{
  background:#fff!important;border:1px solid #e4e8ed!important;
  box-shadow:0 3px 12px #1c283008!important;
  transition:transform .23s ease,border-color .23s ease,box-shadow .23s ease,background .23s ease;
}
.ws-frame>.app .note,.ws-frame>.app .warn,.ws-frame .sim-alert,.ws-frame .tc-note{
  background:#fff!important;color:#515c68!important;border:1px solid #e6e9ed!important;
}
.ws-frame>.app .btn.alt,.ws-frame>.app button.alt,.ws-frame>.app .btnlink{
  background:#f5f6f8!important;color:#28323d!important;border:1px solid #e3e7ec!important
}
.ws-frame>.app input,.ws-frame>.app select,.ws-frame>.app textarea,
.ws-frame>.app pre,.ws-frame .sim-tablewrap{background:#fff!important;color:#242a33;border-color:#dfe4e9}
.ws-frame>.app .sim-tag.warn{background:#f3f5f7;color:#485564}
.ws-frame .ws-user{background:#f2f4f6;color:#343e49;border-color:#e3e8ee}
.ws-frame .ws-filter.active{background:#f4f6f8!important;color:#25303b!important;border-color:#c5cdd6!important}
.ws-frame .ws-row-action{background:#f4f6f8;color:#2f3a45;border-color:#dce2e8}
.ws-frame .ws-row-action:hover{background:#edf0f4}
.ws-frame .ws-tabs a.active{color:#293541}
.ws-frame .ws-tabs a.active::after{background:#586577}
.ws-frame>.app .status{border-left-color:#64748b}
.ws-frame>.app h1{color:#1c2530;font-weight:800}
.ws-frame>.app h2{color:#242d38;font-weight:760}
.ws-frame>.app .card p,.ws-frame>.app .panel p{color:#5d6875}
.ws-frame>.app input:focus-visible,.ws-frame>.app textarea:focus-visible,
.ws-frame>.app select:focus-visible{outline:2px solid #8894a3;outline-offset:1px;border-color:#8894a3}
.ws-frame>.app .tabs button.active{background:#303844;color:#fff}
.ws-frame>.app .tabs button:not(.active){background:#f3f5f7;color:#343f4b}
.ws-frame>.app .tabs button:hover,.ws-frame>.app nav a:hover{border-color:#c8d0d9}
.ws-frame>.app button,.ws-frame>.app .btn{transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease,background .2s ease}
.ws-frame>.app button:hover:not(:disabled),.ws-frame>.app .btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 7px 18px #1b273011}
.ws-frame>.app button:active:not(:disabled){transform:translateY(0)}
.ws-frame>.app{animation:ws-page-enter .24s ease-out both}
@keyframes ws-page-enter{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
@media(hover:hover) and (pointer:fine){
 .ws-frame .ws-kpi:hover,.ws-frame>.app .card:hover,.ws-frame>.app .panel:hover,.ws-frame .sim-counter:hover{
   transform:translateY(-3px);border-color:#c6ced9!important;
   box-shadow:0 12px 24px #16213113!important;
 }
 .ws-frame .sim-table tbody tr:hover,.ws-frame .ws-table tbody tr:hover{background:#f7f8fa}
}
@media(prefers-reduced-motion:reduce){
 .ws-frame>.app{animation:none!important}
 .ws-frame .ws-kpi,.ws-frame>.app .card,.ws-frame>.app .panel,.ws-frame .sim-counter,
 .ws-frame>.app button,.ws-frame>.app .btn{transition:none!important;transform:none!important}
}
@media(prefers-reduced-motion:reduce){.ws-rail-link{transition:none}}

/* UI detail acceptance: readable supporting text, aligned chrome and touch controls.
   Only layout/typography; no change to API, trading state, or data provenance. */
.ws-frame{--ws-control-radius:9px}
/* The universal nav selector must never impose 128px links in the 56px mobile rail. */
.ws-frame .ws-rail .ws-rail-links{display:flex;flex-direction:column;flex-wrap:nowrap;align-items:stretch;gap:7px;width:100%;padding:0;border:0;border-radius:0;background:transparent}
.ws-frame .ws-rail .ws-rail-link{width:100%;min-width:0;max-width:100%;flex:none;border:0;border-radius:0;margin:0;padding:11px 2px;background:transparent}
.ws-frame .ws-rail-link{font-size:12px;line-height:1.45}
.ws-frame .ws-top-badge{font-size:12px}
.ws-frame .ws-pageheading p{font-size:13px}
.ws-frame .ws-eyebrow{font-size:12px}
.ws-frame .ws-readonly{font-size:12px}
.ws-frame .ws-kpi-top small,.ws-frame .ws-kpi-note{font-size:12px}
.ws-frame .ws-filter{font-size:12px!important;min-height:40px!important;border-radius:var(--ws-control-radius)!important}
.ws-frame .ws-search-label{font-size:12px}
.ws-frame .ws-search-label input{height:40px;min-height:40px;font-size:13px;border-radius:var(--ws-control-radius)}
.ws-frame .ws-table{font-size:13px}
.ws-frame .ws-table th{font-size:12px}
.ws-frame .ws-person-cell small{font-size:12px}
.ws-frame .ws-person-avatar{font-size:12px}
.ws-frame .ws-row-action,.ws-frame .ws-secondary-button{font-size:12px;min-height:40px;border-radius:var(--ws-control-radius)}
.ws-frame .ws-clarification{font-size:12px;line-height:1.6}
.ws-frame .ws-section-label{font-size:12px}
.ws-frame .ws-dialog pre{font-size:12px;line-height:1.6}
.ws-frame .ws-dialog-close{min-height:40px;min-width:40px;border-radius:var(--ws-control-radius)}
.ws-frame .ws-rail-link:focus-visible,
.ws-frame .ws-row-action:focus-visible,
.ws-frame .ws-filter:focus-visible{outline:2px solid #687989;outline-offset:2px}
@media(max-width:760px){
 .ws-frame .ws-rail-link{font-size:11px;min-height:62px}
 .ws-frame .ws-kpi-top small{font-size:12px}
 .ws-frame .ws-tabs a{font-size:12px}
 .ws-frame .ws-table-scroll{overscroll-behavior-x:contain}
}
'''

def wrap_page(page, active):
    """Embed old, functioning body unchanged inside a three-module visual frame."""
    if active not in {"news","trading","external","skill"}:
        raise ValueError("Unknown workspace module")
    if "<body>" not in page or "</body>" not in page or "</style>" not in page:
        raise ValueError("Unexpected standalone page format")
    menu = [
        ("overview", "/", "概览", active=="news"),
        ("review", "/skill", "群聊编剧", active=="skill"),
        ("people", "/skill#tab-people", "65人", False),
        ("news", "/#news-process", "资讯审核", False),
        ("trading", "/trading", "账本", active=="trading"),
        ("external", "/trade-platform", "图片编辑", active=="external"),
    ]
    links="".join(
        '<a class="ws-rail-link'+(" active" if selected else "")+
        '" href="'+href+'" title="'+escape(label)+'"'+(' aria-current="page"' if selected else "")+
        '>'+icon(name)+'<span>'+escape(label)+'</span></a>'
        for name,href,label,selected in menu
    )
    open_frame='''<div class="ws-frame">
      <aside class="ws-rail" aria-label="左侧模块导航">
        <a href="/" class="ws-mark" aria-label="NUVEXA 首页">N<i>X</i></a>
        <nav class="ws-rail-links" aria-label="主模块">'''+links+'''</nav>
      </aside>
      <header class="ws-top">
        <form class="ws-top-search" action="/" method="get" role="search">
          '''+icon("overview")+'''<input aria-label="搜索65人人物" type="search" name="member" maxlength="80" placeholder="搜索65人成员编号、姓名、城市或职业…">
          <button type="submit" aria-label="搜索人物">↵</button>
        </form>
        <div class="ws-top-right"><span class="ws-top-badge">财经内容审核 · 需人工确认</span>
          <span class="ws-user" aria-label="NUVEXA">N</span></div>
      </header>'''
    page=page.replace("</style>",SHELL_CSS+"</style>",1)
    page=page.replace("<body>","<body>"+open_frame,1)
    page=page.replace("</body>","</div></body>",1)
    # Free previews have no persistent disk. Never present draft sessions as durable.
    if __import__("os").environ.get("FINANCE_PREVIEW_EPHEMERAL") == "1":
        note = ('<div role="status" style="margin:6px 0 18px;padding:12px 16px;'
                'border:1px solid #e2c7a6;border-radius:10px;'
                'background:#fff9f0;color:#73512c;font-weight:600">'
                '当前为受密码保护的临时云端预览：页面和功能可以查看，'
                '但尚未连接持久磁盘；请不要保存需要长期保留的正式会话、个人资料或交易记录。'
                '</div>')
        page = page.replace('<main class="app">', '<main class="app">'+note, 1)
        page = page.replace('<div class="app">', '<div class="app">'+note, 1)
        page = page.replace('财经内容审核 · 需人工确认', '临时云端预览 · 非持久存储', 1)
    return page
