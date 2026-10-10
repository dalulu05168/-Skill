#!/usr/bin/env python3
"""Local-first dashboard/API with opt-in password-protected hosted mode."""
import argparse
import base64
import binascii
import hmac
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse, urlsplit, parse_qs

from finance_skill_hub import run_pipeline, rss_intake
from content_routing import routing_snapshot
from finance_skill_generate import generate_draft, model_status
from chennan_writing import (load_profiles, summaries, empty_state, read_state,
                             write_state, make_prompt, validate_messages, adopt, save_doc)
from chennan_writing_ui import PAGE as WRITING_PAGE
from trading_65 import (read_state as read_trade_state, write_state as write_trade_state,
                        summary as trade_summary, snapshot as trade_snapshot, apply as apply_trade)
from trading_center_ui import PAGE as TRADING_PAGE
from workspace_theme import apply_visual_system
from external_trade_ui import PAGE as EXTERNAL_TRADE_PAGE
from workspace_layout import wrap_page
from workspace_overview import dashboard_summary, add_overview

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
.news-review-head{display:flex;gap:10px;flex-wrap:wrap;justify-content:space-between;align-items:center;margin:12px 0}
.news-review-status{font-size:12px;color:#586472}
.news-review-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:12px 0 18px}
.news-review-card{background:#fff;border:1px solid #dfe5eb;border-radius:13px;padding:14px;min-width:0;box-shadow:0 3px 12px #1d293908}
.news-review-card:hover{border-color:#bfcad5;transform:translateY(-2px);box-shadow:0 9px 20px #1d293911}
.news-review-card strong{display:block;font-size:13px;color:#28333e;line-height:1.55;margin:7px 0}
.news-review-card small{display:block;color:#687380;font-size:11px;line-height:1.6}
.news-review-card a{display:inline-flex;margin-top:9px;color:#30485d;font-weight:700;font-size:12px;text-decoration:underline}
.news-review-tag{display:inline-block;font-size:10px;border:1px solid #d8dfe7;border-radius:99px;background:#f5f7f9;color:#435363;padding:3px 9px;font-weight:800}
@media(max-width:800px){.news-review-grid{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.news-review-card:hover{transform:none}}
.field{margin-top:14px}.smallinput{margin-top:9px} .warn{font-size:12px;color:#896323;background:#fbf8ef;border-radius:12px;padding:13px 16px;margin-top:26px}
@media(max-width:730px){.grid{grid-template-columns:1fr}.app{padding:20px 17px 50px}.top{flex-wrap:wrap}.panel{padding:20px}}
</style></head><body><main class="app">
<div class="top"><div><div class="logo">NUVEXA <span style="color:#aa832d">FINANCE</span></div>
<div class="tag">罗马尼亚财经 · 统一 SKILL 工作台</div></div><div class="pill">本地审核模式 · 不对外发布</div></div>
<nav class="row" aria-label="工作台模块"><a class="btn active" style="text-decoration:none" href="/" aria-current="page">📰 新闻推送与审核</a><a class="btn alt" style="text-decoration:none;border:1px solid #b99a62" href="/trading">💹 交易中心 · 65人人物</a><a class="btn alt" style="text-decoration:none" href="/trade-platform">↗ 外部交易平台</a></nav>
<section class="panel" style="margin-top:22px;border-color:#dfd6c4;background:#fffdf9">
<h2>65人群聊导演 · 使用现有 ChatGPT / 自定义 GPT</h2>
<p style="font-size:13px">不需要安装Ollama：进入财经 Skill，选择65位人物中适合本话题的成员，生成附有各人完整档案与已采用历史的提示词；将GPT返回的JSON粘贴回工作台，进行个人口吻、连续记忆、结构与来源审查，再由你确认正式采用。GPT无法读取GitHub时，使用页面已经打包进提示词的人物资料；未经来源核实的财经信息仍需审核。</p>
<a href="/skill" class="btn" style="display:inline-block;text-decoration:none">进入财经 Skill · 群聊编剧与记忆 →</a>
</section>
<h1>财经资讯 × 65人独立人格 × 专业课程</h1><p>新闻候审、来源核验要求、16节点课程、65人身份约束与最终质量门禁由同一流程协调。只展示真实执行结果，不编造行情或 AI 生成内容。</p>
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
<p style="font-size:12px">可选连接本地Ollama真实生成教育草稿；无模型时仅完成规则审核。仍无授权行情接口及对外自动发布服务。</p>
<h2>新闻与指标 · 重要性候审</h2><p class="news-review-status">只筛选可能影响市场的事件。标题分级不等于真实新闻；必须核对原文、日期、数据及罗马尼亚传导影响。当前不自动群发。</p><div id="news-review-summary" class="news-review-head"></div><div id="news-review-grid" class="news-review-grid" aria-live="polite"></div><h2>本次任务完整审核包</h2><pre id="result">运行后显示原始候审、指标核验、缺失证据与发布闸门。</pre>
<button id="copy" class="btn alt">复制审核JSON</button></section>
</div>
<section class="panel" style="margin-top:18px"><h2>本地 AI 教育草稿 · 可选功能</h2>
<p style="font-size:13px">只有本机 Ollama 和模型实际安装后才可生成。助理、教授和65名虚构成员分别调用原有规则，始终留在内部审核状态。</p>
<div class="grid" style="margin-top:10px">
<div>
<label for="airole"><small>生成角色</small></label>
<select id="airole"><option value="assistant">助理 · 教育分析草稿</option><option value="professor">教授 · 19:30晚课讲稿片段</option><option value="member">65人虚构成员 · 单人短句</option></select>
<label for="person"><small>成员编号（仅虚构成员需要，01–65）</small></label>
<input id="person" class="smallinput" inputmode="numeric" placeholder="例如 07" maxlength="2" style="width:100%;border:1px solid #dcdde0;border-radius:11px;padding:12px">
</div>
<div>
<label for="aimodel"><small>本地模型（必须预先下载到电脑）</small></label>
<select id="aimodel"><option value="qwen2.5:1.5b">Qwen 2.5 1.5B</option><option value="qwen2.5:0.5b">Qwen 2.5 0.5B</option></select>
<label for="ailang"><small>稿件语言</small></label>
<select id="ailang"><option value="zh">中文审阅稿</option><option value="ro">罗马尼亚语模拟稿</option></select>
</div>
</div>
<label for="aitopic"><small>教育主题（仅作为写作题目，不当作市场事实）</small></label>
<textarea id="aitopic" placeholder="例如：为什么短线交易需要先确认成交量、风险边界与失效条件？" style="min-height:75px"></textarea>
<div class="row"><button id="modelcheck" class="btn alt">检查本机模型</button><button id="generate" class="btn">生成内部教育草稿</button></div>
<div class="status" id="aistatus">当前尚未检测本机模型。</div>
<pre id="airesult">未生成任何内容。联网市场事实、行情和自动群发均不由此模型完成。</pre>
</section>
<div class="warn">数据真实性规则：RSS抓取成功不等于核实正文；人物仅用于标注的虚构教学演绎；运行任务与已发布内容严格区分。</div></main>
<script>
const node=document.querySelector('#node'),status=document.querySelector('#status'),result=document.querySelector('#result');
let last=null;
for(let i=1;i<=16;i++){let opt=document.createElement('option');opt.value='RO-'+String(i).padStart(2,'0');opt.textContent=opt.value;node.append(opt)}
function paintNewsReview(packet){
  const holder=document.querySelector('#news-review-grid'),summary=document.querySelector('#news-review-summary');
  holder.replaceChildren();summary.replaceChildren();
  const news=packet.news||{},items=news.items||[],high=items.filter(x=>['P0','P1'].includes(x.materiality?.tier_candidate));
  const held=items.filter(x=>x.review_priority==='hold_metadata_review');
  const stat=document.createElement('strong');
  stat.textContent='高影响候审 '+(news.high_impact_review_candidates||0)+' 条 · 元数据待补 '+held.length+' 条 · 普通 '+items.filter(x=>x.materiality?.tier_candidate==='P2').length+' 条 · 原始版本 '+(news.raw_pending_versions||0)+' 条';
  summary.append(stat);
  const badge=document.createElement('span');badge.className='news-review-tag';
  badge.textContent='全部未核实 · 发送 0 条';summary.append(badge);
  if(!items.length){const p=document.createElement('p');p.textContent='暂无可审阅项目。未执行抓取不代表市场没有新闻。';holder.append(p);return;}
  const viewed=[...high,...held.filter(x=>!high.includes(x))].slice(0,12);
  if(!viewed.length){const p=document.createElement('p');p.textContent='本批没有识别出重大/重要事件候选。普通资讯仍留在原始审核包，不能据此声称没有市场风险。';holder.append(p);return;}
  for(const item of viewed){
    const card=document.createElement('article');card.className='news-review-card';
    const tag=document.createElement('span');tag.className='news-review-tag';
    tag.textContent=item.review_priority==='hold_metadata_review'?'时间/资料待核查':item.materiality.tier_candidate+' 需人工核查';
    const title=document.createElement('strong');title.textContent=item.display_title||item.title;
    const meta=document.createElement('small');
    meta.textContent='发布时间：'+(item.published_at||'未获取')+' · '+item.materiality.event_category_candidate;
    const reason=document.createElement('small');reason.textContent='核验重点：'+item.materiality.significance_reason+'；罗马尼亚市场影响尚未确认。';
    const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';
    link.textContent='打开原文核查 ↗';
    card.append(tag,title,meta,reason,link);holder.append(card);
  }
}
async function run(fetch){
  const buttons=[document.querySelector('#local'),document.querySelector('#fetch')];
  buttons.forEach(b=>b.disabled=true);status.textContent='正在执行本地工作流…';
  try{
    const spec=document.querySelector('#payload').value.trim()?JSON.parse(document.querySelector('#payload').value):{};
    const response=await fetchApi('/api/prepare',{spec,node:node.value||null,fetch_rss:fetch});
    last=response;const r=response.review;
    paintNewsReview(response);
    status.textContent='执行完成：'+r.status+'；待审新闻 '+response.news.pending_count+' 条；目标栏目 '+response.slot.id+'（'+response.slot.publication+' 罗马尼亚时间）。';
    result.textContent=JSON.stringify({slot:response.slot,news:response.news,market_metadata_audit:response.market_metadata_audit,characters:response.characters,review:response.review},null,2);
  }catch(e){document.querySelector('#news-review-grid').replaceChildren();document.querySelector('#news-review-summary').textContent='数据来源失败，禁止推送';status.textContent='执行失败：'+e.message;result.textContent='没有生成合格的任务包，请核对输入或网络。'}
  finally{buttons.forEach(b=>b.disabled=false)}
}
async function fetchApi(path,payload){let r=await window.fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});let j=await r.json();if(!r.ok)throw Error(j.error||'HTTP '+r.status);return j}
document.querySelector('#local').onclick=()=>run(false);document.querySelector('#fetch').onclick=()=>run(true);
document.querySelector('#copy').onclick=()=>{if(last&&navigator.clipboard)navigator.clipboard.writeText(JSON.stringify(last,null,2));};
const aistatus=document.querySelector('#aistatus'), airesult=document.querySelector('#airesult');
document.querySelector('#modelcheck').onclick=async()=>{
 aistatus.textContent='正在检查电脑本机 Ollama…';
 try{const r=await window.fetch('/api/model/status');const data=await r.json();
 aistatus.textContent=data.can_generate?'可用：'+data.supported_installed.join(', '):
 '未就绪：'+data.remedy;
 }catch(e){aistatus.textContent='本地模型检查失败：'+e.message}
};
document.querySelector('#generate').onclick=async()=>{
 const btn=document.querySelector('#generate');btn.disabled=true;
 aistatus.textContent='正在调用本地模型生成（仅内部草稿，不会发送）…';
 airesult.textContent='模型正在计算，页面可继续查看其他内容。';
 try{
  const payload={role:document.querySelector('#airole').value,
   person_id:document.querySelector('#person').value.trim()||null,
   topic:document.querySelector('#aitopic').value.trim(),
   model:document.querySelector('#aimodel').value,
   language:document.querySelector('#ailang').value,
   node:node.value||null};
  if(payload.role!=='member')payload.person_id=null;
  const data=await fetchApi('/api/generate',payload);
  aistatus.textContent=data.status==='HOLD_FOR_HUMAN_REVIEW'?
    '本地模型已真实返回草稿；必须人工审核，不可自动发布':
    '草稿未通过基础安全检查，已拦截';
  airesult.textContent=JSON.stringify(data,null,2);
 }catch(e){aistatus.textContent='未生成草稿：'+e.message;airesult.textContent='没有成功生成的AI稿件。'}
 finally{btn.disabled=false}
};
</script></body></html>'''


def make_handler(data_dir, *, public_mode=False, auth_username=None, auth_password=None):
    if public_mode and (not auth_username or not auth_password):
        raise ValueError("Hosted mode requires an access username and password")
    state_path = data_dir / "bvb-news-review-state.json"
    report_path = data_dir / "latest-internal-review.json"
    writing_path = data_dir / "chennan-writing-65.json"
    trade_path = data_dir / "trading-65.json"
    run_lock = Lock()  # Avoid concurrent RSS/state writes from separate browser tabs.
    model_lock = Lock()  # Avoid concurrent requests consuming local-model memory.

    class Handler(BaseHTTPRequestHandler):
        def _authorized(self):
            raw = self.headers.get("Authorization", "")
            if not raw.startswith("Basic "):
                return False
            try:
                decoded = base64.b64decode(raw[6:], validate=True).decode("utf-8")
            except (ValueError, UnicodeDecodeError, binascii.Error):
                return False
            username, sep, password = decoded.partition(":")
            return bool(sep) and hmac.compare_digest(username, auth_username) and hmac.compare_digest(password, auth_password)

        def _challenge(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Private Finance Workspace", charset="UTF-8"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def respond(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if public_mode and urlsplit(self.path).path != "/healthz" and not self._authorized():
                self._challenge()
                return
            if urlsplit(self.path).path == "/":
                body = wrap_page(apply_visual_system(add_overview(PAGE)), "news").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; form-action 'self'")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/trading":
                body = wrap_page(apply_visual_system(TRADING_PAGE), "trading").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; form-action 'self'")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path in ("/skill", "/writing"):
                # Editorial scripts, courses, accepted conversations and role memory
                # live in Skill, not on the trading buy/sell dashboard.
                editorial = (WRITING_PAGE
                    .replace("<title>交易中心 · 65人统一交易与人物工作台</title>",
                             "<title>财经 Skill · 课程、群聊与记忆</title>")
                    .replace("NUVEXA <span>· 交易中心</span>",
                             "NUVEXA <span>· 财经 Skill</span>")
                    .replace("交易中心 · 统一交易与人物工作台",
                             "财经 Skill · 课程、群聊与记忆")
                    .replace('data-tab="script">脚本撰写',
                             'data-tab="script">群聊脚本')
                    .replace('data-tab="docs">写作文档',
                             'data-tab="docs">课程资料与文档')
                    .replace('data-tab="history">正式会话与记忆',
                             'data-tab="history">正式会话与人物记忆')
                    .replace('data-tab="people">65人人物库', 'data-tab="people">65人完整档案')
                    .replace('href="/trading" aria-current="page"',
                             'href="/skill" aria-current="page"'))
                body = wrap_page(apply_visual_system(editorial), "skill").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; form-action 'self'")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/trade-platform":
                body = wrap_page(apply_visual_system(EXTERNAL_TRADE_PAGE), "external").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; "
                                 "object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'self'")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/content/categories":
                try:
                    self.respond(200, routing_snapshot())
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(503, {"error": str(exc)})
            elif self.path == "/api/dashboard/summary":
                try:
                    with run_lock:
                        summary = dashboard_summary(data_dir)
                    self.respond(200, summary)
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(503, {"error": str(exc)})
            elif self.path == "/api/trading/sim/state":
                try:
                    with run_lock:
                        ledger = read_trade_state(trade_path)
                        profiles = load_profiles()
                        result = trade_summary(ledger, profiles)
                    self.respond(200, result)
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(409, {"error": str(exc)})
            elif urlsplit(self.path).path == "/api/trading/sim/snapshot":
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    day = query.get("date", [None])[0] or None
                    offer_id = query.get("offer_id", [None])[0] or None
                    with run_lock:
                        ledger = read_trade_state(trade_path)
                        result = trade_snapshot(ledger, day, offer_id)
                    self.respond(200, result)
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(400, {"error": str(exc)})
            elif self.path in ("/api/trading/people", "/api/writing/people"):
                try:
                    p = load_profiles()
                    self.respond(200, {"roster_source": "finance-director-65-v4.1",
                                       "count": len(p), "people": summaries(p)})
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(503, {"error": str(exc)})
            elif (self.path.startswith("/api/trading/profile?") or self.path.startswith("/api/writing/profile?")):
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    requested = query.get("character_id", [""])[0]
                    p = load_profiles()
                    if requested not in p:
                        raise ValueError("Unknown person ID")
                    self.respond(200, {"character_id": requested, "profile": p[requested]})
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(400, {"error": str(exc)})
            elif self.path in ("/api/trading/state", "/api/writing/state"):
                try:
                    with run_lock:
                        state = read_state(writing_path)
                    self.respond(200, {"roster_source": state["roster_source"],
                                       "revision": state["revision"], "docs": state["docs"],
                                       "sessions": state["sessions"]})
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    self.respond(409, {"error": str(exc)})
            elif self.path == "/api/model/status":
                self.respond(200, model_status())
            elif self.path == "/healthz":
                self.respond(200, {"status": "ok", "mode": "password_protected_hosted_review" if public_mode else "loopback_internal_review_only"})
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            if public_mode and not self._authorized():
                self._challenge()
                return
            if self.path not in ("/api/prepare", "/api/generate",
                                 "/api/trading/prompt", "/api/trading/validate",
                                 "/api/trading/adopt", "/api/trading/docs",
                                 "/api/trading/sim/action",
                                 "/api/writing/prompt", "/api/writing/validate",
                                 "/api/writing/adopt", "/api/writing/docs"):
                self.respond(404, {"error": "Not found"})
                return
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if not public_mode and not (host.startswith("127.0.0.1:") or host.startswith("localhost:")):
                self.respond(403, {"error": "Only loopback host is allowed"})
                return
            if origin:
                parsed = urlparse(origin)
                scheme = "https" if public_mode else "http"
                if (parsed.scheme != scheme or parsed.netloc != host or
                        (not public_mode and parsed.hostname not in ("127.0.0.1", "localhost"))):
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
                if self.path == "/api/generate":
                    with model_lock:
                        draft = generate_draft(
                            topic=request.get("topic"),
                            role=request.get("role", "assistant"),
                            model=request.get("model", "qwen2.5:1.5b"),
                            node=request.get("node"),
                            language=request.get("language", "zh"),
                            person_id=request.get("person_id"),
                        )
                        rss_intake.write_json(data_dir / "latest-ai-draft-internal.json", draft)
                    self.respond(200, draft)
                    return
                if self.path == "/api/trading/sim/action":
                    with run_lock:
                        ledger = read_trade_state(trade_path)
                        profiles = load_profiles()
                        output = apply_trade(ledger, profiles, request.get("action"), request)
                        write_trade_state(trade_path, ledger)
                        revision = ledger["revision"]
                    self.respond(200, {"result": output, "revision": revision, "simulation_only": True})
                    return
                if (self.path.startswith("/api/trading/") or self.path.startswith("/api/writing/")):
                    with run_lock:
                        state = read_state(writing_path)
                        profiles = load_profiles()
                        if self.path in ("/api/trading/prompt", "/api/writing/prompt"):
                            prompt, changed = make_prompt(request, profiles, state)
                            if self.path == "/api/trading/prompt":
                                ledger = read_trade_state(trade_path)
                                snapshot = trade_snapshot(ledger, request.get("date"))
                                selected = {str(value).zfill(2) for value in request.get("selected_ids", [])}
                                prompt["trade_facts"] = [fact for fact in snapshot["facts"]
                                                         if fact["character_id"] in selected]
                                prompt["trade_fact_source"] = "trading-65-confirmed-simulation-only"
                                prompt["instructions"].append(
                                    "角色若提及已买入、持仓或卖出，仅可引用trade_facts内有证据的本角色模拟记录；"
                                    "没有记录就不得编造交易、收益或账户状态；所有交易对话标明虚构教学模拟。"
                                )
                            write_state(writing_path, changed)
                            output = {"prompt": prompt, "revision": changed["revision"]}
                        elif self.path in ("/api/trading/validate", "/api/writing/validate"):
                            draft = state["drafts"].get(request.get("draft_id"))
                            if not draft:
                                raise ValueError("Draft missing; generate a new writing prompt")
                            output = validate_messages(request.get("response"), draft, profiles, state["sessions"])
                        elif self.path in ("/api/trading/adopt", "/api/writing/adopt"):
                            if request.get("confirmed") is not True:
                                raise ValueError("Explicit confirmation required")
                            accepted = dict(request.get("response") or {})
                            accepted["confirmed"] = True
                            session, changed = adopt(accepted, request.get("draft_id"), state, profiles)
                            write_state(writing_path, changed)
                            output = {"session": session, "revision": changed["revision"]}
                        elif self.path in ("/api/trading/docs", "/api/writing/docs"):
                            doc, changed = save_doc(request, state)
                            write_state(writing_path, changed)
                            output = {"doc": doc, "revision": changed["revision"]}
                    self.respond(200, output)
                    return
                spec = request.get("spec", {})
                fetch = request.get("fetch_rss", False)
                if not isinstance(fetch, bool):
                    raise ValueError("fetch_rss must be boolean")
                with run_lock:
                    result = run_pipeline(spec, node_id=request.get("node"), fetch_rss=fetch,
                                          state_file=state_path if fetch else None)
                    rss_intake.write_json(report_path, result)
                self.respond(200, result)
            except (ValueError, TypeError, KeyError, OSError, RuntimeError, json.JSONDecodeError) as exc:
                self.respond(400, {"error": str(exc)})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--data-dir", default=os.environ.get(
        "FINANCE_DATA_DIR", str(Path.home() / ".romania-finance-skill-hub")))
    args = parser.parse_args()
    public_mode = args.host not in ("127.0.0.1", "localhost", "::1")
    username = os.environ.get("FINANCE_ACCESS_USER", "admin") if public_mode else None
    password = os.environ.get("FINANCE_ACCESS_PASSWORD") if public_mode else None
    if public_mode and (not password or len(password) < 16):
        parser.error("Public binding requires FINANCE_ACCESS_PASSWORD of at least 16 characters")
    folder = Path(args.data_dir).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(
        folder, public_mode=public_mode, auth_username=username, auth_password=password))
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Finance SKILL dashboard listening on {args.host}:{args.port} ({'hosted/authenticated' if public_mode else 'loopback'})")
    if args.open_browser:
        webbrowser.open(url)
    print(f"Review data directory: {folder}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
