#!/usr/bin/env python3
"""RSS / Atom / RDF フィードを読み、直近の記事一覧を出力する（軸A用）。

スケジュール実行では WebFetch の許可確認に誰も答えられず止まるため、
フィードと記事本文はこのスクリプトで直接取得する。

使い方:
    python3 scripts/fetch_feeds.py                  # 全フィード、直近36時間
    python3 scripts/fetch_feeds.py --hours 24
    python3 scripts/fetch_feeds.py --json           # JSON で出力
    python3 scripts/fetch_feeds.py --article URL    # 記事本文（テキスト）と公開日を出力

取得できなかったフィードは最後に「FAILED: 媒体名 (理由)」として出力する。
"""
import argparse
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

FEEDS = [
    ("ITmedia NEWS", "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"),
    ("INTERNET Watch", "https://internet.watch.impress.co.jp/data/rss/1.0/iw/feed.rdf"),
    ("PC Watch", "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf"),
    ("日経クロステック", "https://xtech.nikkei.com/rss/index.rdf"),
    ("Publickey", "https://www.publickey1.jp/atom.xml"),
    ("gihyo.jp", "https://gihyo.jp/feed/rss2"),
    ("JPCERT/CC", "https://www.jpcert.or.jp/rss/jpcert-all.rdf"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("The Register", "https://www.theregister.com/headlines.atom"),
]

UA = "Mozilla/5.0 (compatible; it-news-digest/1.0)"
JST = timezone(timedelta(hours=9))


def get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_feed(data: bytes):
    root = ET.fromstring(data)
    items = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        title = link = date = desc = ""
        for c in el:
            name = local(c.tag)
            text = (c.text or "").strip()
            if name == "title":
                title = text
            elif name == "link":
                href = c.get("href")
                if href and (c.get("rel") in (None, "alternate")):
                    link = link or href
                elif text:
                    link = link or text
            elif name in ("pubDate", "date", "published", "updated", "issued"):
                if not date or name in ("pubDate", "published"):
                    date = text
            elif name in ("description", "summary", "content", "encoded") and not desc:
                desc = text
        if not link:
            link = el.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "")
        items.append({
            "title": strip_tags(title),
            "url": link,
            "published": parse_date(date),
            "desc": strip_tags(desc)[:200],
        })
    return items


def fetch_one(feed, since):
    name, url = feed
    try:
        items = parse_feed(get(url))
    except Exception as e:  # noqa: BLE001
        return name, None, f"{type(e).__name__}: {e}"
    recent = [i for i in items if i["published"] and i["published"] >= since]
    return name, recent, None


def run_feeds(hours: int, as_json: bool) -> int:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda f: fetch_one(f, since), FEEDS))

    failed = [(n, err) for n, _, err in results if err]
    if as_json:
        out = {
            "fetched_at": now.astimezone(JST).isoformat(timespec="minutes"),
            "hours": hours,
            "items": [
                {**i, "source": n, "published": i["published"].astimezone(JST).isoformat(timespec="minutes")}
                for n, items, _ in results if items for i in items
            ],
            "failed": [{"source": n, "error": e} for n, e in failed],
        }
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for n, items, err in results:
            if err:
                continue
            print(f"## {n} ({len(items)}件)")
            for i in sorted(items, key=lambda x: x["published"], reverse=True):
                ts = i["published"].astimezone(JST).strftime("%m-%d %H:%M")
                print(f"- [{ts} JST] {i['title']}\n  {i['url']}")
                if i["desc"]:
                    print(f"  {i['desc']}")
            print()
        for n, e in failed:
            print(f"FAILED: {n} ({e})")
    return 0 if len(failed) < len(FEEDS) else 1


class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg"}

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.meta = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("property") or a.get("name") or a.get("itemprop")
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"])
        elif tag == "time" and a.get("datetime"):
            self.meta.setdefault("time", a["datetime"])
        if tag in ("p", "br", "h1", "h2", "h3", "li", "div"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.depth:
            self.parts.append(data)


DATE_KEYS = ["article:published_time", "datePublished", "pubdate", "date",
             "dc.date", "DC.date.issued", "parsely-pub-date", "sailthru.date", "time"]


def run_article(url: str, max_chars: int) -> int:
    try:
        raw = get(url)
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {url} ({type(e).__name__}: {e})")
        return 1
    text = raw.decode("utf-8", errors="replace")
    m = re.search(r'charset=["\']?([\w-]+)', text[:3000], re.I)
    if m and m.group(1).lower() not in ("utf-8", "utf8"):
        try:
            text = raw.decode(m.group(1), errors="replace")
        except LookupError:
            pass
    p = TextExtractor()
    p.feed(text)
    published = next((p.meta[k] for k in DATE_KEYS if k in p.meta), "")
    if not published:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', text)
        published = m.group(1) if m else ""
    body = re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t\r\f\v]+", " ", "".join(p.parts))).strip()
    print(f"TITLE: {strip_tags(p.title)}")
    print(f"PUBLISHED: {published or '(不明)'}")
    print(f"URL: {url}\n")
    print(body[:max_chars])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=36)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--article", metavar="URL")
    ap.add_argument("--max-chars", type=int, default=6000)
    a = ap.parse_args()
    if a.article:
        return run_article(a.article, a.max_chars)
    return run_feeds(a.hours, a.json)


if __name__ == "__main__":
    sys.exit(main())
