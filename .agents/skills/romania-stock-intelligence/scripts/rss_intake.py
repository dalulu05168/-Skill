#!/usr/bin/env python3
"""Opt-in BVB RSS ingestion. Produces an UNVERIFIED review queue only."""
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

FEEDS = {
    "BVB_NEWS_RSS": "https://www.bvb.ro/Rss/StiriBVB.ashx",
    "BVB_FINANCIAL_RSS": "https://www.bvb.ro/Rss2/LastFinancialData.ashx?lang=ro",
}
HOSTS = {"bvb.ro", "www.bvb.ro", "iris.bvb.ro"}
KEYWORDS = ("suspendare", "insolven", "faliment", "dividend", "majorare",
            "rezultate financiare", "preluare", "delisting", "bankruptcy", "takeover")
ATOM = "{http://www.w3.org/2005/Atom}"


def _text(node, name):
    child = node.find(name)
    return (child.text or "").strip() if child is not None else ""


def _utc(value):
    if not value:
        return None
    try:
        date = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return date.astimezone(timezone.utc).isoformat() if date.tzinfo else None


def _official(url):
    p = urlsplit(url)
    try:
        return (p.scheme == "https" and p.hostname in HOSTS
                and p.port in (None, 443) and not p.username and not p.password)
    except ValueError:
        return False


def _canonical_article_url(url):
    """Ignore fragment/case of URL host, retain article-defining path and query."""
    p = urlsplit(url)
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))


def parse_feed(payload, source_id):
    """Data from a fixture is not proof of BVB authorship."""
    if source_id not in FEEDS:
        raise ValueError("Source ID is not registered")
    if len(payload) > 4_000_000:
        raise ValueError("Feed is too large")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("Malformed feed XML") from exc
    if root.tag == "rss":
        entries = root.findall("./channel/item")
        atom = False
    elif root.tag == ATOM + "feed":
        entries = root.findall(ATOM + "entry")
        atom = True
    else:
        raise ValueError("Unsupported RSS/Atom feed")
    if not entries:
        raise ValueError("No feed entries; cannot infer no market news")
    result = []
    for item in entries:
        if atom:
            links = [e.get("href", "") for e in item.findall(ATOM + "link")
                     if e.get("rel", "alternate") == "alternate"]
            url = links[0] if links else ""
            title = _text(item, ATOM + "title")
            identifier = _text(item, ATOM + "id") or url
            description = _text(item, ATOM + "summary")
            published = _text(item, ATOM + "published") or _text(item, ATOM + "updated")
        else:
            url = _text(item, "link")
            title = _text(item, "title")
            identifier = _text(item, "guid") or url
            description = _text(item, "description")
            published = _text(item, "pubDate")
        if not title or not _official(url):
            continue
        key = hashlib.sha256((source_id + "\n" + identifier).encode()).hexdigest()
        digest = hashlib.sha256(("\n".join([title, description, published,
                                             _canonical_article_url(url)])).encode()).hexdigest()
        summary = re.sub(r"\s+", " ", title + " " + description).casefold()
        result.append({
            "item_id": key, "source_id": source_id, "url": url, "guid": identifier,
            "title": title, "summary": description, "published_at": _utc(published),
            "digest": digest, "urgency_hint": ("priority_review_candidate"
                if any(word in summary for word in KEYWORDS) else "routine_review"),
            "evidence_status": "unverified_requires_original_article_review",
        })
    if not result:
        # Never silently call an unparsable live feed "no news". Report only link
        # origins/short paths, not untrusted body text, for source-format diagnosis.
        samples = []
        for entry in entries[:4]:
            raw = (_text(entry, "link") if not atom else
                   next((tag.get("href", "") for tag in entry.findall(ATOM + "link")), ""))
            link = urlsplit(raw)
            samples.append(f"{link.scheme or 'relative'}://{link.hostname or '-'}{link.path[:72]}")
        raise ValueError(f"No valid BVB article links among {len(entries)} feed entries; origins={samples}")
    return result


def triage(items, history=None, acknowledgments=None):
    """Keep every unreviewed article version until explicitly acknowledged.

    v1 only tracked seen digests; an unchanged v1 article is requeued once
    on migration because seeing a story never proved that it was reviewed.
    Acknowledging an item records review workflow completion, NOT verification
    of the article or permission to publish it.
    """
    history = history or {}
    previous = dict(history.get("entries", {}))
    updated = dict(previous)
    pending = dict(history.get("pending", {}))
    legacy = history.get("version", 1) < 2
    seen = set()
    for article in items:
        k = article["item_id"]
        if k in seen:
            continue
        seen.add(k)
        old = previous.get(k)
        status = "new" if old is None else ("unchanged" if old == article["digest"] else "revised")
        updated[k] = article["digest"]
        token = k + ":" + article["digest"]
        if status != "unchanged" or (legacy and old is not None):
            pending.setdefault(token, {
                **article,
                "change_state": "legacy_unreviewed" if status == "unchanged" else status,
                "review_required": True,
            })
    for ack in acknowledgments or []:
        if not isinstance(ack, dict) or not isinstance(ack.get("item_id"), str) or not isinstance(ack.get("digest"), str):
            raise ValueError("Acknowledgment must include item_id and digest strings")
        token = ack["item_id"] + ":" + ack["digest"]
        if token not in pending:
            raise ValueError("Acknowledgment does not match a pending article version")
        del pending[token]
    return {"version": 2, "entries": updated, "pending": pending}, list(pending.values())

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def official_fetch(source_id):
    """Only listed HTTPS URLs; rejects redirects instead of following arbitrary targets."""
    url = FEEDS[source_id]
    request = Request(url, headers={"User-Agent": "RomaniaStockIntelligence-RSSReview/1.0"})
    with build_opener(NoRedirect()).open(request, timeout=12) as response:
        if response.geturl() != url:
            raise ValueError("Untrusted redirect")
        payload = response.read(4_000_001)
    if len(payload) > 4_000_000:
        raise ValueError("Feed is too large")
    return payload


def write_json(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description="BVB official RSS -> manual news review only")
    p.add_argument("--source-id", required=True, choices=tuple(FEEDS))
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", help="Offline snapshot (source identity not attested)")
    mode.add_argument("--fetch", action="store_true", help="Explicitly fetch BVB official feed")
    p.add_argument("--state", help="Durable dedup state and pending queue outside repository")
    p.add_argument("--ack-file", help="Explicit human-reviewed article versions JSON (does not verify facts)")
    p.add_argument("--out", help="All still-pending review items JSON path; otherwise stdout")
    args = p.parse_args(argv)
    if args.ack_file and not args.state:
        p.error("--ack-file requires --state so review decisions persist")
    try:
        payload = Path(args.input).read_bytes() if args.input else official_fetch(args.source_id)
        prior = json.loads(Path(args.state).read_text(encoding="utf-8")) if args.state and Path(args.state).exists() else {}
        acknowledgments = []
        if args.ack_file:
            decision = json.loads(Path(args.ack_file).read_text(encoding="utf-8"))
            if not isinstance(decision, dict) or not isinstance(decision.get("acknowledged"), list):
                raise ValueError("Acknowledgments must be a JSON object with acknowledged list")
            acknowledgments = decision["acknowledged"]
        state, rows = triage(parse_feed(payload, args.source_id), prior, acknowledgments)
        report = {
            "feed_url": FEEDS[args.source_id], "source_id": args.source_id,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "source_attestation": ("local_snapshot_not_authenticated" if args.input
                else "official_feed_fetched_not_article_verified"),
            "publish_status": "blocked_pending_manual_evidence_review",
            "items": rows,
        }
        # Persist pending items before replacing the output file, so an output
        # error cannot silently mark unseen items as handled.
        if args.state:
            write_json(args.state, state)
        if args.out:
            write_json(args.out, report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("RSS FAIL:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
