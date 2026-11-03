# ITニュース朝刊

毎朝、国内外のIT・テック系ニュースから重要な10件を選んで日本語で要約し、HTMLにするリポジトリ。
スケジュール実行から「今日の号を作って」と頼まれたら、下の手順をそのまま実行する。

## 毎朝の手順

1. 現在の日時を確認する（タイムゾーンは Asia/Tokyo）。以下、今日の日付を `DATE`（YYYY-MM-DD）とする。
2. `data/DATE.json` がすでにあれば作り直さず、手順 6 から実行する。
3. ニュースを集める（下の「ニュースの集め方」に従う）。
4. 上位10件を選び、`data/DATE.json` を書く（下の「JSONの形式」に従う）。
5. `python3 scripts/build.py DATE` を実行する。ERROR が出たら JSON を直して再実行する。
6. `git add -A && git commit -m "ITニュース朝刊 DATE"` して push する。
7. `docs/daily/DATE.html` を SendUserFile で送る（status は "proactive"、display は "render"、caption は「ITニュース朝刊 DATE」）。
   GitHub アプリでは HTML がコードとして表示されるため、チャット上でページとして開けるようにする。
8. 1位〜3位の見出しと trend を短く報告して終わる。

## ニュースの集め方（2軸）

対象は直近24〜36時間に公開された記事。次の2つの軸で候補を集め、最後に突き合わせる。

### 軸A: RSSフィードを WebFetch で読む

下の各フィードを WebFetch で開き、直近36時間以内の項目の「見出し・URL・公開日時」を抜き出す。
同じURLはスケジュール実行の依頼文にも書いてある（WebFetch は依頼文や検索結果に出てきたURLしか開けないため）。

フィードが開けなかったときは、その媒体名で WebSearch し（例: 「ITmedia NEWS 最新記事」）、
検索結果に出てきた新着一覧ページか記事ページを WebFetch で開いて代わりにする。
それでも取れなかった媒体名は最後の報告に書く。

| 媒体 | フィードURL |
| --- | --- |
| ITmedia NEWS | https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml |
| INTERNET Watch | https://internet.watch.impress.co.jp/data/rss/1.0/iw/feed.rdf |
| PC Watch | https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf |
| 日経クロステック | https://xtech.nikkei.com/rss/index.rdf |
| Publickey | https://www.publickey1.jp/atom.xml |
| gihyo.jp | https://gihyo.jp/feed/rss2 |
| JPCERT/CC | https://www.jpcert.or.jp/rss/jpcert-all.rdf |
| The Verge | https://www.theverge.com/rss/index.xml |
| TechCrunch | https://techcrunch.com/feed/ |
| Ars Technica | https://feeds.arstechnica.com/arstechnica/index |
| BleepingComputer | https://www.bleepingcomputer.com/feed/ |
| The Register | https://www.theregister.com/headlines.atom |

### 軸B: 検索エンジン（WebSearch）

次のトピックごとに分けて WebSearch する（まとめて1回で検索しない）。
日本語と英語の両方のクエリを使い、クエリには今日の日付か「today」「最新」を入れる。

AI / セキュリティ（脆弱性・インシデント） / クラウド / 半導体・ハードウェア / 開発ツール・OSS・言語 / ITビジネス（提携・買収・決算・規制）

軸Aのフィードにない媒体（Reuters、Bloomberg、各社の公式ブログ、Microsoft のセキュリティ更新情報など）の記事はこちらで拾う。

### 突き合わせ

1. 軸Aと軸Bの候補を1つのリストにまとめ、同じ出来事を報じた記事を1件にまとめる。
2. 両方の軸に出てきた出来事、複数の媒体が報じている出来事は重要度が高い目安にする。
3. 上位候補は WebFetch で本文を開き、公開日と内容を確認してから要約する。公開日が確認できない記事は使わない。
4. 使わないもの: まとめ記事・ランキング記事・広告記事・SEO目的の記事・出典のはっきりしないブログ。

## 選び方

- 影響の大きさで順位を付ける: 利用者数、業界への波及、エンジニアの実務への影響、セキュリティ上の緊急度。
- 同じ出来事を報じた複数の記事は1件にまとめ、一番詳しい一次報道を url にする。
- 1つのカテゴリに偏りすぎないようにする（同じカテゴリは原則4件まで）。
- 読み手は Windows 環境中心のソフトウェア開発者。C++ / .NET / Python / 組み込みに関わる話題は優先度を少し上げる。

## JSONの形式

`data/DATE.json`:

```json
{
  "date": "2026-11-03",
  "generated_at": "2026-11-03T07:20+09:00",
  "trend": "10件全体から見える今日の傾向を1〜2文",
  "items": [
    {
      "rank": 1,
      "category": "AI",
      "title": "簡潔な日本語の見出し",
      "summary": "2〜3文の要約",
      "why": "エンジニア目線でなぜ重要かを1文",
      "source": "媒体名",
      "url": "https://...",
      "published": "2026-11-02"
    }
  ]
}
```

- category は `AI` / `セキュリティ` / `クラウド` / `ハード` / `ビジネス` / `開発` / `その他` のいずれか。
- rank は 1〜10 の連番。
- summary は原文の翻訳や引用ではなく、自分の言葉で書く。数値・製品名・社名は元記事どおりにする。
- 10件集まらない日は集まった件数で作り、報告にその旨を書く。

## 触らないもの

- `template/page.html` と `scripts/build.py` は、ユーザーに頼まれたときだけ変更する。
- `docs/` は build.py の出力。手で編集しない。
