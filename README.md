# power-policy-watcher

電力制度の公式サイトを毎日巡回し、新着トピックのタイトル・URL・抜粋をGmailに送信するツール。
GitHub Actionsで毎朝JST 07:00（UTC 22:00）に自動実行されます。

## 巡回対象サイト

| サイト名 | URL |
|---|---|
| 資源エネルギー庁 | https://www.enecho.meti.go.jp/category/electricity_and_gas/electric/summary/ |
| OCCTO（広域的運営推進機関） | https://www.occto.or.jp/information-library/ |
| 電力・ガス取引監視等委員会 | https://www.emsc.meti.go.jp/info/ |

---

## セットアップ手順

### 1. Gmailアプリパスワードの作成

1. Googleアカウントの [セキュリティ設定](https://myaccount.google.com/security) を開く
2. 「2段階認証プロセス」を有効化（未設定の場合）
3. 検索バーで「アプリパスワード」を検索して開く
4. アプリ名（例: `power-policy-watcher`）を入力して「作成」をクリック
5. 表示された16桁のパスワードを控える

### 2. GitHub Secretsの登録

リポジトリの **Settings > Secrets and variables > Actions** で以下を登録します。

| Secret名 | 内容 |
|---|---|
| `GMAIL_FROM` | 送信元Gmailアドレス（例: `you@gmail.com`） |
| `GMAIL_TO` | 送信先メールアドレス |
| `GMAIL_APP_PASSWORD` | 手順1で取得した16桁のアプリパスワード |

### 3. 要約モードの設定（任意）

**Settings > Secrets and variables > Actions > Variables** タブで変数を登録します。

| Variable名 | 値 | 説明 |
|---|---|---|
| `SUMMARIZER_MODE` | `none`（デフォルト） | 要約なし、抜粋をそのまま使用 |
| `SUMMARIZER_MODE` | `sumy` | sumy + Janome による抽出型要約 |

---

## 要約モードの切替

環境変数 `SUMMARIZER_MODE` で切り替えます。

```bash
# 要約なし（デフォルト）
SUMMARIZER_MODE=none python main.py

# sumy + Janome による抽出型要約
SUMMARIZER_MODE=sumy python main.py
```

`sumy` モードは `sumy` と `janome` パッケージを使用し、日本語テキストをLSAアルゴリズムで3文に要約します。
サイトに excerpt（本文抜粋）がない場合は要約対象がないため `none` と同じ結果になります。

---

## cronスケジュール

`.github/workflows/daily.yml` の設定:

```yaml
cron: "0 22 * * *"   # UTC 22:00 = JST 07:00
```

GitHub ActionsのcronはUTC基準です。UTC 22:00はJST翌日07:00に相当します。
スケジュールは `workflow_dispatch` でも手動実行が可能です。

---

## サイト構造変更時のセレクタ調整

各サイトのHTMLが変更された場合は `config/sites.yaml` のセレクタを修正します。

```yaml
sites:
  - name: 資源エネルギー庁
    list_selector: "ul.newsList li"   # ← ニュース一覧の各行要素
    title_selector: "a"               # ← タイトルテキストを含む要素
    link_selector: "a"                # ← href を持つ要素
    excerpt_selector: null            # ← 抜粋テキスト要素（なければ null）
```

調整の手順:
1. ブラウザの開発者ツール（F12）で対象サイトを開く
2. 新着記事の一覧部分を右クリック > 「検証」
3. 適切なCSSセレクタを特定して `sites.yaml` を更新
4. ローカルで `python main.py` を実行して動作確認

---

## ローカル実行

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数を設定して実行
export GMAIL_FROM="you@gmail.com"
export GMAIL_TO="dest@example.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
python main.py
```

履歴は `data/history.json` に保存されます。初回実行時は全件が新着として扱われます。

---

## ディレクトリ構成

```
power-policy-watcher/
├── .github/workflows/daily.yml   # GitHub Actions ワークフロー
├── main.py                       # エントリーポイント
├── core/
│   ├── fetcher.py                # HTTP取得（UA/タイムアウト/sleep設定）
│   ├── parser.py                 # HTML解析・アイテム抽出
│   ├── diff.py                   # 新着差分検出・履歴管理
│   ├── summarizer_none.py        # 要約なしモード
│   ├── summarizer_sumy.py        # sumy抽出型要約モード
│   └── mailer.py                 # Gmail SMTP送信
├── config/sites.yaml             # 巡回対象サイト定義
├── data/history.json             # 送信済みURL履歴（自動更新）
├── requirements.txt
└── .gitignore
```
