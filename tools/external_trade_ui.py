"""External trade website access module.

This module intentionally does not frame, proxy, authenticate, scrape, trade,
or synchronize with an unverified external service.
"""
EXTERNAL_TRADE_URL = "https://trade.sasakic.cc/"

PAGE = r'''<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>外部交易平台 · NUVEXA FINANCE</title>
<style>
:root{font-family:Inter,"Microsoft YaHei",system-ui,sans-serif;color:#272b30;background:#f5f6f8}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:linear-gradient(125deg,#fafafa,#f4f5f7 60%,#f3f8f6)}
.app{max-width:1520px;margin:auto;padding:28px clamp(16px,2.5vw,38px) 60px}
.top{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #e0e4e6;padding-bottom:18px}
.logo{font-size:27px;font-weight:800;letter-spacing:.025em;color:#252a30}.logo span{color:#99773e}
.tag{color:#8b6f3f;font-size:12px;letter-spacing:.12em;font-weight:700}
nav{display:flex;flex-wrap:wrap;gap:8px}
nav a{color:#525963;text-decoration:none;font-weight:700;font-size:13px;border:1px solid #e1e5e7;border-radius:9px;background:#fff;padding:11px 16px}
nav a.active{background:#2b3038;color:#fff}
h1{font-size:clamp(28px,3.3vw,41px);line-height:1.25;margin:35px 0 8px}
h2{font-size:18px;margin:0 0 9px;line-height:1.4}
p{color:#646a72;line-height:1.8;margin:0}
.grid{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(290px,.8fr);gap:18px;margin:24px 0}
.panel{background:#fff;border:1px solid #e2e5e7;border-radius:17px;padding:26px;box-shadow:0 10px 36px #34435408}
.address{display:inline-flex;max-width:100%;overflow-wrap:anywhere;align-items:center;padding:11px 13px;border-radius:9px;background:#f5f7f7;border:1px solid #e5e8e8;color:#1e6866;font-weight:700;font-size:14px;margin:17px 0}
.row{display:flex;gap:11px;flex-wrap:wrap;align-items:center;margin-top:18px}
.action{display:inline-flex;min-height:43px;align-items:center;justify-content:center;gap:7px;background:#1d7774;color:#fff;text-decoration:none;border-radius:10px;padding:11px 19px;font-weight:750;font-size:13px}
.action.alt{background:#f2f5f5;color:#2e6e6a;border:1px solid #d8e6e3}
.action:hover{background:#12635e}
.action.alt:hover{background:#eaf1ef}
.meta{display:flex;align-items:center;gap:10px;border-bottom:1px solid #eef0f1;padding:14px 0;font-size:13px}
.meta strong{margin-left:auto;text-align:right;color:#4e5960}
.notice{margin-top:20px;padding:15px 17px;border:1px solid #e3e4e5;border-left:3px solid #1d7774;border-radius:9px;background:#fafcfc;color:#555e64;font-size:13px;line-height:1.85}
.note{font-size:12px;color:#777f84;margin-top:22px}
@media(max-width:790px){.grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.app{padding:17px 15px 38px}.panel{padding:19px}nav{width:100%}nav a{flex:1;text-align:center}}
</style></head>
<body><main class="app">
<div class="top"><div><div class="logo">NUVEXA <span>FINANCE</span></div><div class="tag">统一工作台 · 第三方交易平台入口</div></div>
<nav aria-label="工作台模块">
<a href="/">📰 新闻推送</a>
<a href="/trading">💹 交易中心</a>
<a href="/trade-platform" class="active" aria-current="page">↗ 外部交易平台</a>
</nav></div>
<h1>外部交易平台</h1>
<p>已纳入统一工作台导航，独立访问第三方网站，不改变新闻推送、交易中心或65人人物数据。</p>
<div class="grid">
<section class="panel" aria-labelledby="platform-heading">
<h2 id="platform-heading">SASAKIC Trade · 网站入口</h2>
<p>目标站点由第三方提供。此页面不代理登录，不保存密码，也不获取其持仓、资金或交易信息。</p>
<div class="address">https://trade.sasakic.cc/</div>
<div class="row">
<a class="action" href="https://trade.sasakic.cc/" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer" aria-label="新标签页打开外部交易平台">打开交易平台 ↗</a>
<a class="action alt" href="/trading">返回交易中心</a>
</div>
<div class="notice">网站内容、可访问性、登录状态及嵌入策略尚未验证。为避免白屏、跨站限制和账号风险，当前不使用 iframe 强行嵌入，也不声称已完成数据或交易接口对接。</div>
</section>
<aside class="panel" aria-labelledby="boundary-heading">
<h2 id="boundary-heading">接入范围</h2>
<div class="meta"><span>导航与入口</span><strong>已接入本工作台</strong></div>
<div class="meta"><span>第三方网站运行</span><strong>由目标站点负责</strong></div>
<div class="meta"><span>第三方账户与交易</span><strong>不接入、不传输</strong></div>
<div class="meta"><span>65人人物系统</span><strong>维持独立来源</strong></div>
<div class="meta"><span>新闻核验/审核</span><strong>原有流程保留</strong></div>
<p class="note">在外部网站的任何登录或交易行为都由用户直接在该站点完成；本地统一工作台无法代表它保证订单执行或账户安全。</p>
</aside>
</div></main></body></html>'''
