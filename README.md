# ITニュース朝刊

Claude Code のスケジュール実行で、毎朝6時に国内外のITニュース上位10件を要約し、HTMLにして保存するリポジトリです。

## 構成

| パス | 内容 |
| --- | --- |
| `CLAUDE.md` | 毎朝の手順（ニュースの集め方・選び方・出力形式） |
| `data/YYYY-MM-DD.json` | その日の10件の要約データ |
| `template/page.html` | HTMLテンプレート |
| `scripts/build.py` | JSON を検証して HTML を生成 |
| `docs/index.html` | 最新号 |
| `docs/daily/YYYY-MM-DD.html` | 各日の号 |
| `docs/archive.html` | バックナンバー一覧 |

## 手動で作る

```
python3 scripts/build.py            # 最新の data から生成
python3 scripts/build.py 2026-11-03 # 日付を指定
```

## スマホで見る

GitHub Pages を `main` ブランチの `/docs` フォルダで公開すると、`docs/index.html` がそのまま最新号のページになります。
