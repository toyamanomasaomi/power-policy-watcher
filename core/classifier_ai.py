"""
Claude API を使った高精度分類器（案B）。
CLASSIFIER_MODE=ai と ANTHROPIC_API_KEY を設定して利用。
案Aのclassifier_keyword.pyとは完全に独立しており、互いに影響しない。
"""
import os
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "あなたは電力システムの専門家です。"
    "ニュースのタイトルを読み、一般送配電事業者が業務システムの"
    "変更・改修対応を迫られる可能性があるかどうかを判断してください。"
)

USER_PROMPT = """\
以下のニュースタイトルについて判断してください。

タイトル：{title}

一般送配電事業者のシステム変更対応が必要な可能性がある場合は「要注意」、
そうでない場合は「通常」とだけ答えてください。"""


def classify(item: dict) -> bool:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY が未設定のため AI 分類をスキップします")
        return False

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_PROMPT.format(title=item["title"]),
            }],
        )
        result = message.content[0].text.strip()
        logger.debug("AI classification '%s' → %s", item["title"], result)
        return "要注意" in result
    except Exception as e:
        logger.warning("AI 分類失敗 '%s': %s", item["title"], e)
        return False
