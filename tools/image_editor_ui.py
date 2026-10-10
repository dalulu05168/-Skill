"""Embed the existing Brantone Veylor PNG notification editor without duplicating it."""
from external_trade_ui import EXTERNAL_TRADE_URL as IMAGE_EDITOR_URL

PAGE = r"""<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>图片编辑 · NUVEXA</title>
<style>
:root{font-family:Inter,"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;color:#26313e;background:#fff}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:#26313e}
.app{max-width:1520px;margin:auto;padding:24px clamp(16px,2.5vw,38px) 45px}
h1{font-size:clamp(24px,2.4vw,32px);line-height:1.35;margin:20px 0 9px;color:#202a36}
p{color:#516070;line-height:1.65;margin:0}
.studio-head{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.studio-caption{font-size:13px}
.studio-action{min-height:42px;display:inline-flex;align-items:center;padding:10px 16px;background:#f4f6f8;
 border:1px solid #cdd6df;border-radius:9px;color:#253240;font-weight:750;font-size:13px;text-decoration:none}
.studio-action:hover{background:#e9eef2}
.studio-note{border:1px solid #e1e7ed;background:#f9fafb;border-radius:10px;padding:10px 14px;margin:16px 0;
 color:#52606d;font-size:12px;line-height:1.7}
.studio-shell{border:1px solid #dfe5ec;border-radius:12px;background:#fff;overflow:hidden;
 box-shadow:0 5px 18px #1723330b}
.studio-shell iframe{display:block;width:100%;height:clamp(740px,calc(100dvh - 230px),1300px);border:0;background:#fff}
@media(max-width:760px){.app{padding:16px 11px 28px}.studio-head{align-items:flex-start}.studio-shell iframe{height:1120px}}
</style></head><body><main class="app">
<section class="studio-head"><div><h1>图片编辑 · 大宗交易通知</h1>
<p class="studio-caption">买入/卖出模板 · TradingView 图表 · 背景上传 · 3840 × 2160 PNG</p></div>
<a class="studio-action" href="https://trade.sasakic.cc/" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">独立窗口打开编辑器 ↗</a></section>
<div class="studio-note">下方显示现有 Brantone Veylor 图片编辑器。编辑和 PNG 导出均由该网站执行；
如因浏览器限制无法显示，请点击右上角“独立窗口打开编辑器”。此模块不接入证券下单，也不共享工作台账号。</div>
<div class="studio-shell"><iframe src="https://trade.sasakic.cc/" title="Brantone Veylor 大宗交易通知图片编辑器"
 loading="eager" referrerpolicy="no-referrer" allow="clipboard-read; clipboard-write"
 sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups" aria-label="图片编辑器"></iframe></div>
</main></body></html>"""
