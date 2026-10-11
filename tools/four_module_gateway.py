"""Four-module front door for the existing finance workspace.

The first visit is an index, not a third-party trading URL or an unverified
dashboard. Navigation never performs trades, messaging, or data mutations.
"""
MODULES=(
    ("01","新闻推送与审核","NEWS & REVIEW","/news",
     "核实罗马尼亚财经资讯、来源和审核结果。无可靠行情时如实显示缺失。"),
    ("02","交易中心","TRADING CENTER","/trading",
     "进入65人模拟交易与持仓工作台。模拟账本不等于真实证券交易。"),
    ("03","财经 Skill","EDITORIAL STUDIO","/skill",
     "课程、群聊教育脚本、正式会话与人物记忆统一管理。"),
    ("04","交易平台","MODULE FOUR","/trade-platform",
     "第四模块保留站内页面，已取消外部交易网站的域名跳转。"),
)
def render_gateway():
    cards="".join(
      '<a class="gate-card" href="'+href+'" aria-label="进入模块'+code+' '+name+'">'
      '<span class="gate-top"><span class="gate-num">'+code+'</span>'
      '<span class="gate-arrow" aria-hidden="true">↗</span></span>'
      '<span class="gate-kind">'+kind+'</span>'
      '<strong>'+name+'</strong><span class="gate-desc">'+desc+'</span>'
      '<span class="gate-enter">进入模块 <span aria-hidden="true">→</span></span></a>'
      for code,name,kind,href,desc in MODULES
    )
    return '''<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>NUVEXA FINANCE · 四合一工作台总入口</title>
<style>
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:linear-gradient(120deg,#fff 5%,#f8f9fb 55%,#eff2f6 100%);
 color:#1c2938;font-family:Inter,"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif}
.gate-page{min-height:100dvh;max-width:1420px;margin:0 auto;padding:clamp(25px,4vw,55px) clamp(16px,4vw,70px);
 display:flex;flex-direction:column;justify-content:center}
.gate-header{display:flex;align-items:center;justify-content:space-between;gap:18px;
 margin-bottom:clamp(21px,3vw,38px)}
.gate-logo{font-weight:850;font-size:clamp(19px,2vw,25px);letter-spacing:.08em}
.gate-logo b{font-weight:850;color:#70829a}
.gate-version{font-size:12px;color:#687686;padding:9px 13px;border:1px solid #e1e7ef;
 border-radius:9px;background:#fff;white-space:nowrap}
.gate-kicker{font-size:12px;font-weight:800;letter-spacing:.18em;color:#73869c;margin:0 0 10px}
h1{font-weight:850;line-height:1.2;letter-spacing:-.025em;font-size:clamp(30px,4.3vw,58px);margin:0}
.gate-intro{margin:15px 0 clamp(23px,3.6vw,45px);color:#6b7887;font-size:clamp(13px,1.1vw,16px);line-height:1.65}
.gate-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(12px,1.7vw,22px)}
.gate-card{min-width:0;min-height:clamp(188px,24vh,260px);display:flex;flex-direction:column;
 background:linear-gradient(146deg,#fff 5%,#fbfcfe 64%,#f3f6fa 100%);
 border:1px solid #dfe5ed;border-radius:16px;box-shadow:0 11px 34px #2334470a;
 padding:clamp(18px,2.3vw,32px);text-decoration:none;color:inherit;
 transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.gate-card:hover,.gate-card:focus-visible{transform:translateY(-3px);border-color:#9ab4d0;
 box-shadow:0 19px 38px #344e6c18}
.gate-card:focus-visible{outline:3px solid #859fbd;outline-offset:3px}
.gate-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.gate-num{color:#4a6686;background:#f1f5fa;border:1px solid #e0e7f0;
 padding:7px 10px;border-radius:8px;font-weight:850;font-size:14px}
.gate-arrow{color:#a3adba;font-size:20px}
.gate-kind{font-size:11px;letter-spacing:.14em;color:#8192a7;font-weight:750;margin-bottom:7px}
.gate-card strong{font-size:clamp(19px,2vw,25px);font-weight:800}
.gate-desc{font-size:13px;color:#637184;line-height:1.58;margin:9px 0 17px}
.gate-enter{font-size:13px;font-weight:800;color:#375d86;margin-top:auto}
.gate-enter span{margin-left:8px}
.gate-footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;
 border-top:1px solid #e4e9ef;margin-top:clamp(18px,2.5vw,30px);padding-top:14px;
 font-size:11px;line-height:1.5;color:#8591a0}
@media(max-width:650px){
 .gate-page{justify-content:flex-start;padding:22px 16px 28px}
 .gate-header{margin-bottom:32px}
 .gate-version{font-size:10px;white-space:normal;text-align:right}
 .gate-grid{grid-template-columns:1fr;gap:11px}
 .gate-card{min-height:174px;padding:18px}
 .gate-top{margin-bottom:8px}.gate-desc{margin:7px 0 9px}
}
@media(prefers-reduced-motion:reduce){.gate-card{transition:none!important}.gate-card:hover{transform:none}}
</style></head><body><main class="gate-page" id="main">
<header class="gate-header"><div class="gate-logo">NUVEXA <b>FINANCE</b></div>
<div class="gate-version">统一入口 · 四个独立模块</div></header>
<section aria-labelledby="gateway-title">
<p class="gate-kicker">ONE WORKSPACE · FOUR MODULES</p>
<h1 id="gateway-title">四合一管理工作台</h1>
<p class="gate-intro">选择需要进入的模块。各模块独立运行，保留现有业务与权限边界。</p>
<nav aria-label="四个业务模块" class="gate-grid">'''+cards+'''</nav>
</section><footer class="gate-footer"><span>NUVEXA · 工作台导航</span>
<span>财经资讯与模拟交易不代表实时行情或已执行证券订单</span></footer>
</main></body></html>'''
