#!/usr/bin/env python3
"""data/YYYY-MM-DD.json から HTML を生成する。

使い方:
    python3 scripts/build.py            # data/ の最新日付で生成
    python3 scripts/build.py 2026-11-03 # 日付を指定

出力:
    docs/daily/YYYY-MM-DD.html  その日の号
    docs/index.html             最新号（同じ内容）
    docs/archive.html           過去の号の一覧
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TEMPLATE = ROOT / "template" / "page.html"

CATEGORIES = {"AI", "セキュリティ", "クラウド", "ハード", "ビジネス", "開発", "その他"}
REQUIRED = ["rank", "category", "title", "summary", "why", "source", "url", "published"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def validate(d: dict, date: str) -> None:
    if d.get("date") != date:
        fail(f"date が {date} ではありません: {d.get('date')!r}")
    if not d.get("trend"):
        fail("trend が空です")
    items = d.get("items")
    if not isinstance(items, list) or not items:
        fail("items が空です")
    if len(items) > 10:
        fail(f"items は10件までです（{len(items)}件）")
    ranks = []
    for i, it in enumerate(items, 1):
        for k in REQUIRED:
            if not it.get(k):
                fail(f"items[{i}] の {k} が空です")
        if it["category"] not in CATEGORIES:
            fail(f"items[{i}] の category が不正です: {it['category']!r}")
        if not str(it["url"]).startswith(("https://", "http://")):
            fail(f"items[{i}] の url が不正です: {it['url']!r}")
        if not DATE_RE.match(str(it["published"])):
            fail(f"items[{i}] の published は YYYY-MM-DD 形式にしてください")
        ranks.append(it["rank"])
    if sorted(ranks) != list(range(1, len(items) + 1)):
        fail(f"rank は 1〜{len(items)} の連番にしてください: {ranks}")
    if len(items) < 10:
        print(f"WARNING: items が {len(items)} 件です", file=sys.stderr)


def render(d: dict, archive_href: str) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    return tpl.replace("__NEWS_DATA__", payload).replace("__ARCHIVE_HREF__", archive_href)


def build_archive(dates: list) -> str:
    rows = []
    for date in dates:
        d = json.loads((DATA / f"{date}.json").read_text(encoding="utf-8"))
        top = d["items"][0]["title"] if d.get("items") else ""
        rows.append(
            f'<li><a href="daily/{date}.html"><span class="d">{date.replace("-", ".")}</span>'
            f'<span class="t">{html.escape(top)}</span></a></li>'
        )
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ITニュース朝刊 バックナンバー</title>
<style>
:root {{ --bg:#f2f4f7; --surface:#fff; --ink:#16202a; --muted:#5a6572; --line:#dce1e8; --accent:#1f5fbf; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0e1318; --surface:#151c23; --ink:#e4e9ef; --muted:#96a2ae; --line:#252f39; --accent:#72a6f3; color-scheme:dark; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Hiragino Sans","Yu Gothic","Meiryo",sans-serif; padding:28px 16px 56px; }}
.wrap {{ max-width:760px; margin:0 auto; }}
h1 {{ font-size:26px; margin:0 0 6px; }}
p {{ color:var(--muted); margin:0 0 20px; font-size:14px; }}
p a {{ color:var(--accent); }}
ul {{ list-style:none; margin:0; padding:0; background:var(--surface); border:1px solid var(--line); border-radius:12px; }}
li + li {{ border-top:1px solid var(--line); }}
li a {{ display:flex; gap:14px; padding:14px 16px; color:inherit; text-decoration:none; }}
li a:hover .t {{ text-decoration:underline; }}
.d {{ font-family:ui-monospace,Menlo,Consolas,monospace; color:var(--accent); flex:none; font-size:13px; padding-top:2px; }}
.t {{ min-width:0; overflow-wrap:anywhere; }}
</style>
</head>
<body><div class="wrap">
<h1>バックナンバー</h1>
<p><a href="index.html">最新号へ</a>　各号の1位の見出しを表示しています。</p>
<ul>
{chr(10).join(rows)}
</ul>
</div></body>
</html>
"""


def main() -> None:
    dates = sorted(p.stem for p in DATA.glob("*.json") if DATE_RE.match(p.stem))
    if not dates:
        fail("data/ に YYYY-MM-DD.json がありません")
    date = sys.argv[1] if len(sys.argv) > 1 else dates[-1]
    src = DATA / f"{date}.json"
    if not src.exists():
        fail(f"{src} がありません")
    try:
        d = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{src.name} のJSONが壊れています: {e}")
    validate(d, date)

    (DOCS / "daily").mkdir(parents=True, exist_ok=True)
    (DOCS / "daily" / f"{date}.html").write_text(render(d, "../archive.html"), encoding="utf-8")
    if date == dates[-1]:
        (DOCS / "index.html").write_text(render(d, "archive.html"), encoding="utf-8")
    (DOCS / "archive.html").write_text(build_archive(sorted(dates, reverse=True)), encoding="utf-8")
    print(f"OK: {date} を生成しました（{len(d['items'])}件）")


if __name__ == "__main__":
    main()
