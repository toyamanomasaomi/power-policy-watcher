"""
キーワードベースの分類器（案A）。
CLASSIFIER_MODE=keyword のときに使用。追加費用なし。
"""
import logging

logger = logging.getLogger(__name__)

# 一般送配電事業者のシステム変更対応が必要となりうるキーワード
ALERT_KEYWORDS = [
    # 系統・接続
    "系統連系", "接続協議", "系統コード", "系統安定化",
    "送電容量", "広域連系", "ノンファーム", "混雑管理",
    "電圧調整", "周波数調整", "保護リレー", "再給電",
    # 市場・取引
    "需給調整市場", "インバランス", "接続供給", "振替供給",
    "容量市場", "ベースロード市場",
    # 計量・メーター
    "計量", "検針", "スマートメーター", "計量法",
    # システム・技術
    "制御システム", "監視システム", "給電システム",
    "技術要件", "技術基準",
    # 制度・規制
    "省令改正", "規程改定", "業務規程", "接続検討",
    "一般送配電", "配電網",
]


def classify(item: dict) -> bool:
    text = item.get("title", "") + " " + item.get("excerpt", "")
    for kw in ALERT_KEYWORDS:
        if kw in text:
            logger.debug("Alert keyword '%s' matched: %s", kw, item["title"])
            return True
    return False
