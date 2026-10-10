"""Shared visual system for the news review and Trading Center modules.

Presentation only: never adds mock metrics, overrides API behavior or mutates data.
The source image reference should be compared in a visual browser QA pass before
claiming pixel-for-pixel fidelity.
"""
UNIFIED_STYLE = r"""
:root{
 --ui-canvas:#ffffff;--ui-ink:#26292e;--ui-muted:#646a73;
 --ui-gold:#3b4652;--ui-gold-soft:#f3f5f7;
 --ui-border:#e0e3e8;--ui-card:#ffffff;
 --ui-radius:16px;--ui-shadow:0 8px 30px rgba(35,42,54,.055);
 font-family:Inter,"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
 color:var(--ui-ink);
}
html{scroll-behavior:smooth}
body{background:#fff;color:var(--ui-ink)}
.app{max-width:1520px;min-height:100vh;margin:0 auto;padding:clamp(18px,2.4vw,36px) clamp(16px,2.4vw,38px) 50px}
.top{padding-bottom:19px;border-bottom:1px solid var(--ui-border);align-items:center}
.logo,.brand{font-size:clamp(23px,2vw,30px);font-weight:800;letter-spacing:.022em;color:#232831;line-height:1.4}
.logo span,.brand span{color:var(--ui-gold)}
.tag,.sub{font-size:12px;letter-spacing:.09em;font-weight:650;color:var(--ui-gold)}
h1{font-size:clamp(28px,3vw,39px);letter-spacing:-.03em;line-height:1.35;margin:29px 0 8px;color:#292d31}
h2{line-height:1.4;letter-spacing:-.012em;font-weight:750}
p{line-height:1.75}
.panel,.card{background:var(--ui-card);border:1px solid var(--ui-border);border-radius:var(--ui-radius);box-shadow:var(--ui-shadow);padding:clamp(18px,1.9vw,26px);transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease}
.grid,.layout{gap:18px}
nav[aria-label="主模块"],nav[aria-label="工作台模块"]{
 display:flex;gap:9px;align-items:center;flex-wrap:wrap;
 background:rgba(255,255,255,.72);border:1px solid var(--ui-border);
 padding:6px;border-radius:13px;
}
nav[aria-label="主模块"] a,nav[aria-label="工作台模块"] a{
 display:inline-flex;align-items:center;justify-content:center;
 min-height:41px;padding:10px 18px;border:1px solid transparent;
 border-radius:9px;background:transparent;color:#646a72;
 text-decoration:none;font-size:13px;font-weight:700;
 transition:background .18s ease,box-shadow .18s ease,color .18s ease,transform .18s ease
}
nav[aria-label="主模块"] a:hover,nav[aria-label="工作台模块"] a:hover{background:#f5f6f8;color:#262a30;transform:translateY(-1px)}
nav[aria-label="主模块"] a.active,nav[aria-label="工作台模块"] a.active{background:#292e36;color:#fff;box-shadow:0 2px 8px #27292b20}
button,.btn{border-radius:10px;min-height:40px;font-weight:700;transition:transform .17s ease,box-shadow .17s ease}
button:hover:not(:disabled),.btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 4px 10px #24282e1a}
button:active:not(:disabled),.btn:active:not(:disabled){transform:translateY(0)}
button.alt,.btn.alt{background:var(--ui-gold-soft);color:#354150}
input,select,textarea{min-height:42px;color:#272a30;border:1px solid #d9dde2;border-radius:10px;background:#fff}
input:focus-visible,select:focus-visible,textarea:focus-visible{
 outline:2px solid var(--ui-gold);outline-offset:1px;border-color:var(--ui-gold)
}
.status{border-left-color:var(--ui-gold)}
.step b,.note{color:var(--ui-gold)}
pre{background:#f8f9fa;border:1px solid #edf0f2;border-radius:12px}
.warn,.note{background:#fff;border:1px solid #e6e9ed;border-radius:11px}
*:focus-visible{outline-offset:2px}
@media (max-width:800px){
 .app{padding:18px 15px 36px}
 .top{align-items:flex-start;gap:15px}
 nav[aria-label="主模块"],nav[aria-label="工作台模块"]{width:100%}
 nav[aria-label="主模块"] a,nav[aria-label="工作台模块"] a{flex:1;min-width:128px}
 .grid,.layout{grid-template-columns:1fr}
 .panel,.card{padding:18px}
}
@media (prefers-reduced-motion:reduce){
 html{scroll-behavior:auto}
 button,.btn,nav a{transition:none!important;transform:none!important}
}
"""

def apply_visual_system(page):
    """Append a single shared token layer to pages with existing inline CSS."""
    if "</style>" not in page:
        raise ValueError("Page is missing a style block")
    return page.replace("</style>", UNIFIED_STYLE + "</style>", 1)
