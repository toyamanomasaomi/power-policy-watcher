# power-policy-watcher — 開発コンテキスト

## 目的
電力制度関連サイトを定期巡回し、新着情報をGmailで通知するPythonツール。
一般送配電事業者のシステム変更対応が必要な記事を自動で「要注意」判定する機能が中心。

## 実行方法

```bash
# 依存パッケージ
pip install -r requirements.txt

# ローカル実行（環境変数を設定してから）
python main.py
```

GitHub Actions で1日1回自動実行（JST 06:00）。

## 環境変数

| 変数名 | 必須 | 説明 |
|---|---|---|
| `GMAIL_FROM` | ○ | 送信元Gmailアドレス |
| `GMAIL_TO` | ○ | 送信先（カンマ区切りで複数可） |
| `GMAIL_APP_PASSWORD` | ○ | Googleアプリパスワード（16桁） |
| `SUMMARIZER_MODE` | - | `none`（デフォルト）/ `sumy` |
| `CLASSIFIER_MODE` | - | `keyword`（デフォルト）/ `ai` |
| `ANTHROPIC_API_KEY` | - | `CLASSIFIER_MODE=ai` のときのみ必要 |

## アーキテクチャ

```
main.py
 └─ サイトごとにループ
     ├─ fetcher.py       HTTP取得（UA偽装・2秒sleep）
     ├─ parser.py        HTML → items（CSSセレクタ）
     ├─ rss_parser.py    RSS/Atom → items（feedparser）
     ├─ json_parser.py   JSON API → items
     ├─ diff.py          data/history.json で既読URL管理
     ├─ summarizer_*.py  抜粋の要約（none / sumy+Janome）
     ├─ classifier_*.py  「要注意」判定（keyword / ai）
     └─ mailer.py        Gmail SMTP送信
```

## データソース（config/sites.yaml）

| サイト名 | 取得方式 | URL |
|---|---|---|
| OCCTO | JSON API | `https://www.occto.or.jp/_include/json/news-list.json` |
| 電力・ガス取引監視等委員会 | Google News RSS | （クエリ検索） |
| 資源エネルギー庁 | Google News RSS | （クエリ検索） |

## 主要ファイル

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント、パイプライン制御 |
| `config/sites.yaml` | 巡回対象サイト定義（セレクタ等） |
| `data/history.json` | 送信済みURL履歴（GitHub Actionsが自動コミット） |
| `.github/workflows/daily.yml` | スケジュール実行・history.jsonのpush |
| `core/classifier_keyword.py` | キーワードリスト（ALERT_KEYWORDS）で要注意判定 |
| `core/classifier_ai.py` | Claude Haiku APIで要注意判定 |

## 分類ロジック（classifier）

- `CLASSIFIER_MODE=keyword`（デフォルト）: `ALERT_KEYWORDS` リストとタイトル+抜粋を突合
- `CLASSIFIER_MODE=ai`: Claude Haiku に「要注意 / 通常」を判定させる
- 判定結果 `requires_attention=True` の記事はメール件名・本文で上部に表示

## メール形式

- 件名: `[電力制度] ⚠要注意N件 / 新着M件 (日付)` または `[電力制度] 新着M件 (日付)`
- 本文: 要注意セクション → その他セクションの順に記事一覧

## 開発上の注意

- サイト構造が変わった場合は `config/sites.yaml` のセレクタを修正する
- `data/history.json` はGitHub Actionsが自動コミットするため、ローカルとの競合に注意
- `json_parser.py` は brotli 圧縮を除外している（requests が自動解凍できないため）
