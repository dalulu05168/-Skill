"""Visual login screen for hosted finance workspace and explicitly open UI preview."""
from html import escape

TEMPLATE = r'''<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>登录 · NUVEXA FINANCE</title>
<style>
*{box-sizing:border-box}
:root{color-scheme:light;font-family:Inter,"Microsoft YaHei",system-ui,sans-serif;color:#182636}
html,body{height:100%;margin:0;overflow:hidden}
body{display:grid;place-items:center;background:linear-gradient(120deg,#fff,#f2f4f7)}
.frame{width:min(calc(100vw - 20px),calc((100dvh - 20px) * 16 / 9),1680px);aspect-ratio:16/9;
height:auto;max-height:calc(100dvh - 20px);border:1px solid #dce5ed;background:#fff;
border-radius:16px;box-shadow:0 24px 60px #2737470c;display:grid;grid-template-columns:1.2fr .8fr;overflow:hidden}
.art{position:relative;display:flex;flex-direction:column;padding:clamp(25px,4vw,68px);background:linear-gradient(145deg,#f9fafb,#eff2f5 72%,#e5edf3)}
.brand{font-size:clamp(18px,2vw,27px);font-weight:850;letter-spacing:.12em}.brand span{color:#7990ac}
.deco{position:absolute;inset:10% 10% 20% 20%;border:1px solid #d5dfe9;border-radius:40% 8% 42% 10%;transform:rotate(-13deg);pointer-events:none}
.deco::before,.deco::after{content:"";position:absolute;border:1px solid #cddae7;border-radius:40% 8% 42% 10%;inset:12%;transform:rotate(23deg)}
.deco::after{inset:25%;transform:rotate(-21deg)}
.artcopy{z-index:1;margin-top:auto}.eyebrow{font-size:12px;font-weight:800;letter-spacing:.18em;color:#748ca4}
h1{font-size:clamp(35px,5.2vw,74px);line-height:1.12;margin:13px 0 18px;letter-spacing:-.04em}
.artcopy p{font-size:clamp(13px,1.3vw,17px);color:#748397;line-height:1.7;margin:0}
.formpanel{display:flex;flex-direction:column;justify-content:center;align-items:stretch;padding:clamp(25px,4vw,82px)}
.formpanel h2{font-size:clamp(26px,2.3vw,36px);margin:0 0 9px}
.formpanel>p{color:#7a8998;font-size:13px;line-height:1.7;margin:0 0 25px}
form{display:grid;gap:16px}label{font-size:12px;color:#415267;font-weight:700;display:grid;gap:9px}
input{width:100%;height:46px;padding:0 14px;border:1px solid #d9e3eb;border-radius:9px;background:#fafbfd;color:#17293c;font:inherit;font-size:14px}
input:focus-visible,a:focus-visible,button:focus-visible{outline:2px solid #597ea5;outline-offset:2px}
button,.cta{display:grid;place-items:center;height:48px;margin-top:6px;background:#284665;color:white;border:0;border-radius:9px;font:750 14px Inter,"Microsoft YaHei",sans-serif;cursor:pointer;text-decoration:none}
button:hover,.cta:hover{background:#1c3550}
.note{font-size:11px;color:#8592a1;line-height:1.6;margin:20px 0 0}
.error{font-size:12px;color:#9d3939;margin:0 0 15px}
.demo{padding:18px;border:1px solid #dce5ee;border-radius:12px;background:#f9fafb}
.demo p{font-size:13px;line-height:1.8;color:#5e7187;margin:0}
.demo .cta{margin-top:18px}.footer{margin-top:auto;color:#8a98a7;font-size:11px}
@media(max-width:700px){.frame{height:100dvh;max-height:none;width:100%;aspect-ratio:auto;border:0;border-radius:0;grid-template-columns:1fr;grid-template-rows:minmax(180px,.7fr) minmax(0,1.3fr)}
.art{padding:25px}.artcopy h1{font-size:32px;margin:9px 0}.deco{inset:10% 12% 10% 46%}
.formpanel{padding:25px;justify-content:flex-start}.formpanel>p{margin-bottom:16px}.footer{margin-top:22px}}
</style></head><body>
<main class="frame">
<section class="art" aria-label="欢迎使用 NUVEXA FINANCE"><div class="brand">NUVEXA <span>FINANCE</span></div>
<div class="deco" aria-hidden="true"></div><div class="artcopy"><span class="eyebrow">FOUR MODULES · ONE WORKSPACE</span>
<h1>专业工作台<br>由此开始。</h1><p>资讯 · 交易管理 · 人物 Skill · 图片编辑<br>四个模块，各司其职。</p></div></section>
<section class="formpanel"><h2>欢迎使用</h2><p>NUVEXA FINANCE · 安全工作台入口</p>
{{ERROR}}
{{CONTROLS}}
<div class="footer">NUVEXA · 中文工作台 · 桌面 16:9 · 移动端适配</div></section>
</main></body></html>'''

FORM = """<form action="/login" method="post" autocomplete="on">
<label>登录账号<input name="username" autocomplete="username" required maxlength="100"></label>
<label>登录密码<input name="password" autocomplete="current-password" type="password" required maxlength="200"></label>
<button type="submit">安全登录 →</button></form>
<p class="note">账号由工作台管理员配置；系统不会在页面中公开默认密码。</p>"""

DEMO = """<div class="demo"><p><strong>界面验收预览</strong><br>
这个站点是静态 UI 预览，没有登录认证或业务后端。点击下方按钮可以查看设计，但这不表示已登录。</p>
<a class="cta" href="/workspace/">进入只读界面预览 →</a></div>
<p class="note">正式账号登录需要部署带服务端身份校验的应用。</p>"""

def render_login(*, preview=False, invalid=False):
    controls = DEMO if preview else FORM
    error = '<p class="error">账号或密码不正确，请重新输入。</p>' if invalid and not preview else ""
    return TEMPLATE.replace("{{ERROR}}", error).replace("{{CONTROLS}}", controls)
