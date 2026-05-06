import logging

logger = logging.getLogger(__name__)

SENTENCES_COUNT = 3


def summarize(text: str) -> str:
    if not text.strip():
        return ""
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("japanese"))
        summarizer = LsaSummarizer()
        result = summarizer(parser.document, SENTENCES_COUNT)
        return "".join(str(s) for s in result) or text
    except Exception as e:
        logger.warning("Summarization failed: %s", e)
        return text
