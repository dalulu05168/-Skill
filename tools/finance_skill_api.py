#!/usr/bin/env python3
"""Loopback-only dashboard/API for the unified review hub (not public deployment)."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

from finance_skill_hub import run_pipeline, rss_intake

PAGE = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>罗马尼亚财经 · SKILL 工作台</title>
<style>
:root{font-family:Inter,"Microsoft YaHei",system-ui,sans-serif;color:#272729;background:#f4f5f7}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:linear-gradient(130deg,#fafafa 0%,#f0f1f3 56%,#f6f2e9 100%)}
.app{max-width:1190px;margin:0 auto;padding:38px 28px 64px}
.top{display:flex;justify-content:space-between;align-items:center;gap:14px;border-bottom:1px solid #d7d7d8;padding-bottom:20px}
.logo{font-size:26px;font-weight:800;letter-spacing:.04em;color:#27292b}.tag{font-size:12px;font-weight:700;letter-spacing:.12em;color:#a77925}
.pill{font-size:12px;border:1px solid #c3c4c7;background:white;border-radius:99px;padding:9px 13px;color:#4b4d51}
h1{font-size:clamp(28px,3.5vw,45px);margin:42px 0 12px;line-height:1.28;letter-spacing:-.02em}p{color:#6b6d72;line-height:1.8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:29px}.panel{background:#fff;border:1px solid #e5e5e5;border-radius:20px;padding:28px;box-shadow:0 12px 35px #373a4009}
.panel h2{font-size:17px;margin:0 0 12px}.step{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #f0f0f0;font-size:13px}.step b{color:#9a7029}
.row{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}.btn{cursor:pointer;border:0;border-radius:12px;font-weight:700;padding:13px 17px;font-size:13px;background:#292b30;color:white}.btn.alt{background:#f4eedf;color:#775621}.btn:disabled{opacity:.5;cursor:wait}
select,textarea{width:100%;border:1px solid #dcdde0;border-radius:11px;background:#fff;padding:12px;font:inherit;color:#25272c}select{margin-top:9px}
textarea{resize:vertical;min-height:105px;font-size:12px;margin-top:13px;line-height:1.65}
small{color:#77797d}.status{margin-top:23px;border-left:3px solid #b38940;padding:4px 12px;font-size:13px;color:#44464a}
pre{white-space:pre-wrap;word-break:break-word;background:#f7f7f8;border:1px solid #ededf0;padding:16px;border-radius:12px;max-height:310px;overflow:auto;font-size:12px}
.warn{font-size:12px;color:#896323;background:#fbf8ef;border-radius:12px;padding:13px 16px;margin-top:26px}
@media(max-width:730px){.grid{grid-template-columns:1fr}.app{padding:20px 17px 50px}.top{flex-wrap:wrap}.panel{padding:20px}}
</style></head><body><main class="app">
<div class="top"><div><div class="logo">NUVEXA <span style="color:#aa832d">FINANCE</span></div>
<div class="tag">罗马尼亚财经 · 统一 SKILL 工作台</div></div><div class="pill">本地审核模式 · 不对外发布</div></div>
<h1>一次运行，联动五项审核能力。</h1><p>新闻候审、来源核验要求、16节点课程、65人身份约束与最终质量门禁由同一流程协调。只展示真实执行结果，不编造行情或 AI 生成内容。</p>
<div class="grid">
<section class="panel"><h2>统一任务入口</h2><p style="font-size:13px">可直接检查规则和下一栏目，也可联网读取BVB新闻候审。大盘数字、台词草稿必须由可核实来源提供。</p>
<label for="node"><small>课程节点（留空自动选择下一场）</small></label>
<select id="node"><option value="">自动选择下一节点</option></select>
<label for="payload"><small>可选：输入结构化JSON（news_queue / observations / messages）</small></label>
<textarea id="payload" placeholder='{"messages":[]}'></textarea>
<div class="row"><button id="local" class="btn alt">检查规则及下一栏目</button><button id="fetch" class="btn">抓取BVB并生成审核包</button></div>
<div class="status" id="status">尚未运行。本页面不会自动发布群消息。</div></section>
<section class="panel"><h2>执行链路</h2>
<div class="step"><span>01 · BVB原文核验</span><b>人工证据门禁</b></div>
<div class="step"><span>02 · 新闻重要性及去重</span><b>可执行候审</b></div>
<div class="step"><span>03 · 16节点助理／教授路由</span><b>规则联动</b></div>
<div class="step"><span>04 · 65人角色身份检查</span><b>实际读取</b></div>
<div class="step"><span>05 · 最终审稿及发布闸门</span><b>禁止自动群发</b></div>
<p style="font-size:12px">尚未连接真实生成模型、授权行情接口和对外发布服务，因此不会虚构已经生成的教授或成员发言。</p>
<h2>本次任务结果</h2><pre id="result">运行后显示真实状态、新闻候选数和应人工核实的步骤。</pre>
<button id="copy" class="btn alt">复制审核JSON</button></section>
</div><div class="warn">数据真实性规则：RSS抓取成功不等于核实正文；人物仅用于标注的虚构教学演绎；运行任务与已发布内容严格区分。</div></main>
<script>
const node=document.querySelector('#node'),status=document.querySelector('#status'),result=document.querySelector('#result');
let last=null;
for(let i=1;i<=16;i++){let opt=document.createElement('option');opt.value='RO-'+String(i).padStart(2,'0');opt.textContent=opt.value;node.append(opt)}
async function run(fetch){
  const buttons=[document.querySelector('#local'),document.querySelector('#fetch')];
  buttons.forEach(b=>b.disabled=true);status.textContent='正在执行本地工作流…';
  try{
    const spec=document.querySelector('#payload').value.trim()?JSON.parse(document.querySelector('#payload').value):{};
    const response=await fetchApi('/api/prepare',{spec,node:node.value||null,fetch_rss:fetch});
    last=response;const r=response.review;
    status.textContent='执行完成：'+r.status+'；待审新闻 '+response.news.pending_count+' 条；目标栏目 '+response.slot.id+'（'+response.slot.publication+' 罗马尼亚时间）。';
    result.textContent=JSON.stringify({slot:response.slot,news:response.news,market_metadata_audit:response.market_metadata_audit,characters:response.characters,review:response.review},null,2);
  }catch(e){status.textContent='执行失败：'+e.message;result.textContent='没有生成合格的任务包，请核对输入或网络。'}
  finally{buttons.forEach(b=>b.disabled=false)}
}
async function fetchApi(path,payload){let r=await window.fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});let j=await r.json();if(!r.ok)throw Error(j.error||'HTTP '+r.status);return j}
document.querySelector('#local').onclick=()=>run(false);document.querySelector('#fetch').onclick=()=>run(true);
document.querySelector('#copy').onclick=()=>{if(last&&navigator.clipboard)navigator.clipboard.writeText(JSON.stringify(last,null,2));};
</script></body></html>'''


def make_handler(data_dir):
    state_path = data_dir / "bvb-news-review-state.json"
    report_path = data_dir / "latest-internal-review.json"
    run_lock = Lock()  # Avoid concurrent RSS/state writes from separate browser tabs.

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; form-action 'none'")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/healthz":
                self.respond(200, {"status": "ok", "mode": "loopback_internal_review_only"})
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            if self.path != "/api/prepare":
                self.respond(404, {"error": "Not found"})
                return
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if origin:
                parsed = urlparse(origin)
                if parsed.scheme != "http" or parsed.netloc != host or parsed.hostname not in ("127.0.0.1", "localhost"):
                    self.respond(403, {"error": "Cross-origin request rejected"})
                    return
            length = self.headers.get("Content-Length", "")
            if (not length.isdigit() or int(length) > 500_000 or
                self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json"):
                self.respond(400, {"error": "JSON request required (max 500 KB)"})
                return
            try:
                request = json.loads(self.rfile.read(int(length)))
                if not isinstance(request, dict):
                    raise ValueError("Request must be an object")
                spec = request.get("spec", {})
                fetch = request.get("fetch_rss", False)
                if not isinstance(fetch, bool):
                    raise ValueError("fetch_rss must be boolean")
                with run_lock:
                    result = run_pipeline(spec, node_id=request.get("node"), fetch_rss=fetch,
                                          state_file=state_path if fetch else None)
                    rss_intake.write_json(report_path, result)
                self.respond(200, result)
            except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
                self.respond(400, {"error": str(exc)})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default=str(Path.home() / ".romania-finance-skill-hub"))
    args = parser.parse_args()
    folder = Path(args.data_dir).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(folder))
    print(f"Finance SKILL dashboard: http://127.0.0.1:{args.port}/")
    print(f"Local-only review data: {folder}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
