# power-policy-watcher 開発ログ

作成日：2026-05-06  
担当AI：Claude Sonnet 4.6

---

## プロジェクト概要

電力制度の公式サイト・関連ニュースを毎日巡回し、新着情報をGmailに自動送信するツール。  
GitHub Actionsで毎日JST 5:00 / 11:00 / 15:00 の3回自動実行。

---

## 最終的なディレクトリ構成

```
power-policy-watcher/
├── .github/workflows/daily.yml   # GitHub Actions スケジュール実行
├── main.py                       # エントリーポイント
├── core/
│   ├── __init__.py
│   ├── fetcher.py                # HTTP取得（HTMLサイト用）
│   ├── parser.py                 # HTML解析
│   ├── rss_parser.py             # RSS/Atom フィード解析
│   ├── json_parser.py            # JSON API 解析
│   ├── diff.py                   # 新着差分検出・history.json管理
│   ├── summarizer_none.py        # 要約なし（デフォルト）
│   ├── summarizer_sumy.py        # sumy+Janome 抽出型要約
│   └── mailer.py                 # Gmail SMTP送信（複数宛先対応）
├── config/sites.yaml             # 巡回対象サイト定義
├── data/
│   ├── .gitkeep
│   └── history.json              # 送信済みURL履歴（自動更新）
├── requirements.txt
├── .gitignore
├── README.md
└── DEVLOG.md                     # 本ファイル
```

---

## 巡回対象サイト（最終設定）

| 順序 | サイト名 | 取得方式 | URL/エンドポイント |
|---|---|---|---|
| 1 | OCCTO（広域的運営推進機関） | JSON API | `occto.or.jp/_include/json/news-list.json` |
| 2 | 電力・ガス取引監視等委員会 | Google News RSS | キーワード検索 |
| 3 | 資源エネルギー庁 | Google News RSS | キーワード検索 |

---

## 主要設定

- **実行時刻**：JST 5:00 / 11:00 / 15:00（UTC 20:00 / 02:00 / 06:00）
- **送信先**：`GMAIL_TO` Secret にカンマ区切りで複数設定可能
- **要約モード**：`SUMMARIZER_MODE` Variable で `none`（デフォルト）または `sumy` を選択
- **取得上限**：200件/サイト（実質全件）

---

## GitHub Secrets 設定

| Secret名 | 内容 |
|---|---|
| `GMAIL_FROM` | 送信元Gmailアドレス |
| `GMAIL_TO` | 送信先（カンマ区切りで複数可）例: `a@gmail.com, b@example.com` |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード（16桁） |

---

## 開発経緯・トラブルシューティング記録

### 問題1：`data/history.json` が存在せず git add が失敗
- **原因**：新着ゼロの場合 `save_history()` を呼ばなかった
- **対策**：`save_history()` を新着有無に関わらず常に呼ぶよう変更
- **対策2**：`git add data/history.json || true` でファイル未存在でも止まらないように

### 問題2：Node.js 20 deprecation 警告
- **対策**：`actions/checkout@v4.2.2`・`actions/setup-python@v5.6.0` に更新

### 問題3：資源エネルギー庁・電力ガス監視委員会がタイムアウト
- **原因**：`enecho.meti.go.jp`・`egc.meti.go.jp` が GitHub Actions の IPをブロック
- **対策**：Google News RSS（`news.google.com/rss/search`）経由に変更

### 問題4：OCCTO が 404
- **原因**：URLが `/information-library/` から `/news/` に変更されていた
- **対策**：`sites.yaml` のURL修正

### 問題5：OCCTO が 0件（HTMLスクレイピング）
- **原因**：ニュース一覧が JavaScript で動的に読み込まれており `requests` では取得不可
- **対策**：ブラウザの Network タブで JSON API エンドポイントを発見
  - `https://www.occto.or.jp/_include/json/news-list.json`
  - `json_parser.py` を新規作成して直接取得

### 問題6：OCCTO JSON が空レスポンス（Referer チェック）
- **原因**：サーバーが `Referer` ヘッダーを検証、自サイト以外からは空を返す
- **対策**：リクエストヘッダーに `Referer: https://www.occto.or.jp/news/` を追加

### 問題7：OCCTO JSON が文字化け（brotli 圧縮）
- **原因**：`Accept-Encoding: gzip, deflate, br` を送信したため brotli 圧縮で返却
  - `requests` は brotli を自動解凍しない
- **対策**：JSON リクエスト時は `Accept-Encoding: gzip, deflate` に限定

---

## GitHub Actions の仕組み

```
GitHubのサーバー（毎日JST 5:00/11:00/15:00）
  ↓ daily.yml を読む
  ↓ Python 環境構築
  ↓ main.py 実行
      ↓ 各サイトから新着取得
      ↓ history.json と差分比較
      ↓ 新着があればGmail送信
  ↓ history.json をコミット・プッシュ
```

**Claude Pro / ライセンスの影響はゼロ。** 実行はすべて GitHub と Gmail が担う。  
GitHub Actions 無料枠：月2000分。本ツールは約180分/月（3回/日×2分×30日）で余裕あり。

---

## PC・環境が変わった場合の復旧手順

1. Git をインストール
2. `git clone https://github.com/toyamanomasaomi/power-policy-watcher.git`
3. 以上（GitHub Actions の自動実行はPCなしで継続している）

ローカルでの手動実行が必要な場合：
```bash
pip install -r requirements.txt
set GMAIL_FROM=your@gmail.com
set GMAIL_TO=dest@example.com
set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
python main.py
```

---

## 残課題

| サイト | 状況 | 備考 |
|---|---|---|
| 資源エネルギー庁 | Google News RSS で代替中 | 公式サイトは GitHub Actions IP をブロック |
| 電力・ガス取引監視等委員会 | Google News RSS で代替中 | 同上 |
| OCCTO | JSON API で公式データ取得済み | 解決済み |

公式サイト直接取得が必要な場合は、自宅PC（タスクスケジューラ）または  
GitHub Actions セルフホストランナーでの実行を検討。
