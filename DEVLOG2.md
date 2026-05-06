# power-policy-watcher 開発ログ 第2章

作成日：2026-05-06  
（DEVLOG.md の続き。メール動作確認以降の記録）

---

## 機能追加・バグ修正の記録

---

### 改善1：複数宛先・1日3回・全差分対応

**変更内容：**

| 項目 | 変更前 | 変更後 |
|---|---|---|
| 取得件数上限 | 20件/サイト | 200件/サイト（実質全件） |
| 表示順 | 資源エネルギー庁→OCCTO→監視委員会 | OCCTO→監視委員会→資源エネルギー庁 |
| 送信先 | 1件のみ | カンマ区切りで複数可 |
| 実行回数 | 1回/日（JST 07:00） | 3回/日（JST 05:00 / 11:00 / 15:00） |

**複数送信先の設定方法：**
GitHub Secrets の `GMAIL_TO` をカンマ区切りで設定する。
```
a@gmail.com, b@example.com, c@example.com
```

**cronスケジュール（UTC基準）：**
```yaml
- cron: "0 20 * * *"   # UTC 20:00 = JST 05:00
- cron: "0 2 * * *"    # UTC 02:00 = JST 11:00
- cron: "0 6 * * *"    # UTC 06:00 = JST 15:00
```

---

### 問題1：OCCTO が JSON 取得できない（空レスポンス）

**エラー：**
```
ERROR JSON fetch error OCCTO: Expecting value: line 1 column 1 (char 0)
```

**原因：**
OCCTOのJSON APIはリクエストの `Referer` ヘッダーを検証しており、
自サイト以外からの直接アクセスには空レスポンスを返す。

**対策：**
`sites.yaml` に `extra_headers` を追加し、Refererを付与した。
```yaml
extra_headers:
  Referer: "https://www.occto.or.jp/news/"
```

---

### 問題2：OCCTO の JSON がバイナリ文字化け（brotli圧縮）

**エラー：**
```
ERROR JSON parse error OCCTO: Expecting value: line 1 column 1 (char 0)
| body: c\n██HMs;████g█...（バイナリ）
```

**原因：**
フェッチャーのヘッダーに `Accept-Encoding: gzip, deflate, br` を設定していたため、
サーバーが brotli 圧縮で返却した。
`requests` ライブラリは gzip/deflate は自動解凍するが、**brotli は解凍できない**。

**対策：**
`json_parser.py` で JSON リクエスト時は brotli を除外するよう上書きした。
```python
headers = {**HEADERS, "Accept-Encoding": "gzip, deflate", **site.get("extra_headers", {})}
```

**結果：**
3サイト合計60件の取得・送信に成功。
```
INFO 資源エネルギー庁: 20 new item(s)
INFO OCCTO（広域的運営推進機関）: 20 new item(s)
INFO 電力・ガス取引監視等委員会: 20 new item(s)
INFO Mail sent. 60 new item(s) total.
```

---

### 改善2：要注意フラグ機能の実装

**目的：**
一般送配電事業者のシステム変更が必要となりうる記事を自動で識別し、
メールの先頭に強調表示する。

---

#### アーキテクチャ

`CLASSIFIER_MODE` 環境変数で分類器を切り替える。案Aと案Bは完全に独立したファイル。

```
CLASSIFIER_MODE=keyword  →  core/classifier_keyword.py（案A・デフォルト）
CLASSIFIER_MODE=ai       →  core/classifier_ai.py    （案B・別途API設定要）
CLASSIFIER_MODE=none     →  分類なし
```

---

#### 案A：キーワードフィルタリング（`classifier_keyword.py`）

- **判定者：Python プログラム（文字列マッチング）**
- **課金：なし**
- タイトル・概要に以下のキーワードが含まれれば「要注意」と判定

```
系統連系 / 接続協議 / 系統コード / 系統安定化 / 送電容量 /
広域連系 / ノンファーム / 混雑管理 / 電圧調整 / 周波数調整 /
保護リレー / 再給電 / 需給調整市場 / インバランス /
接続供給 / 振替供給 / 容量市場 / ベースロード市場 /
計量 / 検針 / スマートメーター / 計量法 /
制御システム / 監視システム / 給電システム /
技術要件 / 技術基準 / 省令改正 / 規程改定 /
業務規程 / 接続検討 / 一般送配電 / 配電網
```

キーワードの追加・削除は `classifier_keyword.py` を編集するだけ。

---

#### 案B：Claude API 分類（`classifier_ai.py`）

- **判定者：Claude Haiku（Anthropic API）**
- **課金：1件あたり約0.01円（月数十円程度）**
- 文脈を読んで判断するため案Aより高精度

**利用開始手順：**
1. `platform.anthropic.com` でAPIキーを取得（Claude Pro とは別契約）
2. GitHub Secrets に `ANTHROPIC_API_KEY` を登録
3. GitHub Variables の `CLASSIFIER_MODE` を `ai` に変更
4. コードの変更は不要

---

#### メールフォーマット変更

**件名：**
```
要注意あり → [電力制度] ⚠要注意3件 / 新着42件 (2026-05-06)
要注意なし → [電力制度] 新着42件 (2026-05-06)
```

**本文構成：**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ 要注意：一般送配電事業者 システム変更の可能性あり（N件）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【OCCTO】 需給調整市場のルール改定について
URL: https://...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ その他の新着情報（N件）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【資源エネルギー庁】 再エネ賦課金の単価について
URL: https://...
```

---

## 現在の課金状況まとめ

| サービス | 用途 | 費用 |
|---|---|---|
| GitHub Actions | 自動実行（3回/日） | 無料（月約180分/2000分枠） |
| Gmail SMTP | メール送信 | 無料 |
| Google News RSS | ニュース取得 | 無料 |
| OCCTO JSON API | ニュース取得 | 無料 |
| Python（requests等） | スクレイピング | 無料 |
| Claude / Anthropic API | **現在は使用していない** | 0円 |

**Claude Pro の有無はこのツールの動作に一切影響しない。**

---

## 最終的なファイル構成

```
core/
├── classifier_keyword.py   ← 案A（現在有効）
├── classifier_ai.py        ← 案B（CLASSIFIER_MODE=ai で有効化）
├── json_parser.py          ← OCCTO用JSONパーサー
├── rss_parser.py           ← Google News RSS パーサー
├── fetcher.py              ← HTML取得（現在は未使用）
├── parser.py               ← HTML解析（現在は未使用）
├── diff.py                 ← 新着差分検出
├── summarizer_none.py      ← 要約なし
├── summarizer_sumy.py      ← sumy要約（SUMMARIZER_MODE=sumy で有効）
└── mailer.py               ← Gmail送信（複数宛先・要注意ハイライト対応）
```

---

## 環境変数一覧（GitHub Variables）

| 変数名 | 値の例 | 説明 |
|---|---|---|
| `CLASSIFIER_MODE` | `keyword`（デフォルト）/ `ai` / `none` | 分類器の選択 |
| `SUMMARIZER_MODE` | `none`（デフォルト）/ `sumy` | 要約器の選択 |

## Secrets 一覧（GitHub Secrets）

| Secret名 | 説明 |
|---|---|
| `GMAIL_FROM` | 送信元Gmailアドレス |
| `GMAIL_TO` | 送信先（カンマ区切りで複数可） |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード（16桁） |
| `ANTHROPIC_API_KEY` | 案B使用時のみ必要 |
