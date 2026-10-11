#!/usr/bin/env python3
"""Cloud-compatible BVB News Desk v3.3 public-news API.

No fabricated quotes, no trading, no publication, no account/session data.
Only fetches known public news/official endpoints; upstream HTTP failures
are returned as explicit failed source statuses. No general-purpose proxy.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from xml.etree import ElementTree as ET

FEEDS = (
 {"id":"bvb-market","name":"BVB 官方市场公告","tier":"official","urls":("https://www.bvb.ro/Rss/StiriBVB.ashx","https://bvb.ro/Rss/StiriBVB.ashx")},
 {"id":"bvb-issuer","name":"BVB 公司财务披露","tier":"official","urls":("https://www.bvb.ro/Rss2/LastFinancialData.ashx?lang=ro","https://www.bvb.ro/Rss2/LastFinancialData.ashx")},
 {"id":"bvb-operation","name":"BVB 交易所公告","tier":"official","urls":("https://www.bvb.ro/Rss/OperatiuniSiComunicateBVB.ashx","https://bvb.ro/Rss/OperatiuniSiComunicateBVB.ashx")},
 {"id":"ecb","name":"欧洲央行公告","tier":"official","urls":("https://www.ecb.europa.eu/rss/press.html",)},
 {"id":"bursa","name":"BURSA 资本市场资讯","tier":"media","urls":("https://www.bursa.ro/_rss/?t=pcaps","https://www.bursa.ro/piata-capital-bursa.xml")},
)
ALLOWED_ORIGINS = frozenset({
 "https://invest.sasakic.cc",
 "https://p004-unified-four-module-preview.onrender.com",
})
ALLOWED_ARTICLE_HOSTS = frozenset({
 "bvb.ro","www.bvb.ro","bursa.ro","www.bursa.ro",
 "ecb.europa.eu","www.ecb.europa.eu",
})
CACHE = {"value":None,"at":0.0}
CACHE_LOCK = threading.Lock()
TRANSLATIONS:dict[str,str]={}
LAST_CALL:dict[str,float]={}
USER_AGENT = "Mozilla/5.0 (compatible; BVBNewsDesk/3.3; NewsReview/1.0)"


def iso_now():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("文章来源发生重定向，请到原始网页人工核验")


def get_url(url, timeout=7, max_bytes=1_500_000, method="GET", data=None, headers=None, allow_redirect=True):
    req = Request(url, data=data, method=method, headers={"User-Agent":USER_AGENT,"Accept":"application/rss+xml, application/xml, text/xml, text/html;q=0.8",**(headers or {})})
    opener = urlopen if allow_redirect else build_opener(NoRedirect()).open
    with opener(req, timeout=timeout) as res:
        payload = res.read(max_bytes+1)
        if len(payload)>max_bytes:
            raise ValueError("上游响应体超过大小限制")
        content_type = res.headers.get_content_charset()
    charset = content_type or "utf-8"
    try: return payload.decode(charset, errors="strict")
    except (LookupError,UnicodeDecodeError): return payload.decode("utf-8-sig",errors="replace")


def field(node, tag):
    for child in node:
        if child.tag.split("}")[-1].split(":")[-1].lower() == tag.lower():
            if tag=="link" and child.attrib.get("href"):
                return child.attrib["href"].strip()
            return " ".join("".join(child.itertext()).split())
    return ""


def clean(text):
    plain=unescape(re.sub(r"(?is)<[^>]*>"," ",text or ""))
    return re.sub(r"\s+"," ",plain).strip()[:900]


def fetch_feed(feed):
    failures=[]
    for attempt,url in enumerate(feed["urls"],1):
        try:
            text=get_url(url)
            if not re.search(r"<(?:rss|feed|rdf:RDF|\?xml)\b",text[:2000],re.I):
                raise ValueError("响应不是有效 RSS/Atom XML")
            root=ET.fromstring(text)
            items=[e for e in root.iter() if e.tag.split("}")[-1].lower() in ("item","entry")]
            if not items: raise ValueError("新闻源未返回任何条目")
            articles=[]
            for node in items[:35]:
                title=clean(field(node,"title"))
                link=field(node,"link")
                u=urlsplit(link)
                if not title or u.scheme not in ("http","https") or not u.hostname:continue
                articles.append({
                    "title":title,"url":link,"description":clean(field(node,"description") or field(node,"summary") or field(node,"content")),
                    "guid":field(node,"guid") or field(node,"id"),
                    "dateRaw":field(node,"pubDate") or field(node,"published") or field(node,"updated"),
                    "sourceId":feed["id"],"source":feed["name"],"tier":feed["tier"],"sourceUrl":url
                })
            if not articles:raise ValueError("未发现带有链接的有效条目")
            status={"id":feed["id"],"name":feed["name"],"url":url,"state":"ok","count":len(articles),
                    "message":f"本次成功{len(articles)}条；使用：{url}","attempts":attempt}
            return articles,status
        except (HTTPError,URLError,TimeoutError,ValueError,ET.ParseError,UnicodeError,OSError) as exc:
            failures.append(f"{url}: {str(exc)[:155]}")
    return [],{"id":feed["id"],"name":feed["name"],"url":feed["urls"][0],"state":"failed","count":0,
                "message":" | ".join(failures)[:360],"attempts":len(failures)}


def quote_bet():
    manual="https://www.bvb.ro/TradingAndStatistics/Trading/MarketsToday"
    q={"state":"unavailable","source":"BVB WebDelayed","url":"https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx?op=GetIndex",
       "manualUrl":manual,"note":"官方接口未返回经核验的 BET 行情；请打开官方页面人工确认",
       "value":None,"change":None,"marketTime":None,"method":None}
    failures=[]
    for method in ("GET","SOAP"):
        try:
            if method=="GET":
                xml=get_url("https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx/GetIndex?code=BET",timeout=6)
            else:
                soap=b'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><GetIndex xmlns="www.bvb.ro"><code>BET</code></GetIndex></soap:Body></soap:Envelope>'
                xml=get_url("https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx",timeout=6,method="POST",data=soap,headers={"SOAPAction":'"www.bvb.ro/GetIndex"',"Content-Type":"text/xml; charset=utf-8"})
            root=ET.fromstring(xml)
            for node in root.iter():
                if node.tag.split("}")[-1]!="TypeIndices" or field(node,"Code")!="BET": continue
                price=float(field(node,"CurrentValue"));pct=float(field(node,"PrcChange"))
                timestamp=field(node,"LastUpdateTime")
                if not (0<price<1_000_000 and abs(pct)<90 and timestamp):
                    raise ValueError("指数或时间戳校验失败")
                q.update(state="ok",value=price,change=pct,marketTime=timestamp,method=method,
                         note="BVB 延迟数据，正式发表前仍须核对交易日及数据授权")
                return q
            raise ValueError("响应不包含有效 BET TypeIndices")
        except (HTTPError,URLError,ValueError,ET.ParseError,TimeoutError,OSError) as exc:
            failures.append(method+": "+str(exc)[:130])
    q["note"]="自动报价不可用："+ "；".join(failures)+"。请打开 BVB 官方页面人工核对"
    return q


def refresh_news():
    now=time.monotonic()
    with CACHE_LOCK:
        if CACHE["value"] and now-CACHE["at"]<270:return CACHE["value"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(fetch_feed, f) for f in FEEDS]
        qf=pool.submit(quote_bet)
        results=[future.result() for future in futures]
        quote=qf.result()
    value={"fetchedAt":iso_now(),"articles":[a for rows,_ in results for a in rows],
           "sources":[state for _,state in results],"quote":quote,"live":True}
    with CACHE_LOCK:CACHE.update(value=value,at=time.monotonic())
    return value


def fetch_article(link):
    u=urlsplit(link)
    if u.scheme!="https" or u.hostname not in ALLOWED_ARTICLE_HOSTS or u.port not in (None,443) or u.username:
        raise ValueError("只允许公开 BVB、BURSA 和 ECB 来源的 HTTPS 文章")
    content=get_url(link,timeout=9,max_bytes=700_000,allow_redirect=False)
    content=re.sub(r"(?is)<(script|style|nav|header|footer|noscript|svg|form|aside)\b[^>]*>.*?</\1>"," ",content)
    content=re.sub(r"(?is)<(p|h1|h2|h3|li|br|div|section)\b[^>]*>","\n",content)
    text=unescape(re.sub(r"(?s)<[^>]*>"," ",content))
    text=re.sub(r"[ \t]+"," ",text)
    text=re.sub(r"(?:\r?\n[ \t]*){3,}","\n\n",text).strip()[:12000]
    if len(text)<90:raise ValueError("自动提取文本过短，请到来源网页人工阅读")
    return {"url":link,"fetchedAt":iso_now(),"content":text,"length":len(text),
            "verified":False,"warning":"机器提取不能代替原文核验"}


def translate_headline(lang,text):
    if lang not in ("ro","en") or not text or len(text)>320 or len(text.encode("utf-8"))>450:
        raise ValueError("翻译参数无效")
    key=lang+"|"+text.strip()
    if key in TRANSLATIONS:
        return {"status":"ok","translated":TRANSLATIONS[key],"provider":"MyMemory","cached":True,"verified":False}
    url="https://api.mymemory.translated.net/get?q="+quote(text.strip(),safe="")+"&langpair="+quote(lang+"|zh-CN",safe="")
    data=json.loads(get_url(url,timeout=9,max_bytes=100_000))
    result=unescape((data.get("responseData") or {}).get("translatedText") or "").strip()
    if data.get("responseStatus")!=200 or not re.search("[\u4e00-\u9fff]",result):
        raise ValueError("机翻供应商未返回可用中文标题")
    if len(TRANSLATIONS)>150:TRANSLATIONS.clear()
    TRANSLATIONS[key]=result
    return {"status":"ok","translated":result,"provider":"MyMemory","cached":False,"verified":False}


class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):pass
    def send_json(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        origin=self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin",origin)
            self.send_header("Vary","Origin")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        u=urlsplit(self.path)
        if u.path in ("/healthz","/api/status"):
            return self.send_json(200,{"ok":True,"version":"3.3","server":"PythonCloud","time":iso_now()})
        if u.path not in ("/api/refresh","/api/article","/api/translate"):
            return self.send_json(404,{"error":"Unknown endpoint"})
        origin=self.headers.get("Origin")
        if origin and origin not in ALLOWED_ORIGINS:
            return self.send_json(403,{"error":"Origin not allowed"})
        args=parse_qs(u.query)
        try:
            if u.path=="/api/refresh":return self.send_json(200,refresh_news())
            if u.path=="/api/article":return self.send_json(200,fetch_article(args.get("url",[""])[0]))
            lang=args.get("lang",[""])[0];title=args.get("text",[""])[0]
            try:return self.send_json(200,translate_headline(lang,title))
            except (ValueError,HTTPError,URLError,TimeoutError) as exc:
                return self.send_json(200,{"status":"unavailable","translated":None,"verified":False,"error":str(exc)[:200]})
        except (ValueError,HTTPError,URLError,TimeoutError,ET.ParseError,OSError) as exc:
            return self.send_json(400,{"error":str(exc)[:200],"verified":False})
        except Exception:
            return self.send_json(500,{"error":"服务异常","verified":False})


if __name__=="__main__":
    port=int(os.environ.get("PORT","18766"))
    server=ThreadingHTTPServer(("0.0.0.0",port),Handler)
    print("BVB v3.3 public-news collector listening on",port,flush=True)
    server.serve_forever()
