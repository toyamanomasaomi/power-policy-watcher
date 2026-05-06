import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


SEP = "━" * 44


def _format_item(item: dict) -> list[str]:
    lines = [f"【{item['site_name']}】 {item['title']}", f"URL: {item['url']}"]
    if item.get("summary"):
        lines.append(f"概要: {item['summary']}")
    lines.append("")
    return lines


def _build_body(items: list[dict]) -> str:
    alert = [i for i in items if i.get("requires_attention")]
    normal = [i for i in items if not i.get("requires_attention")]
    lines = [f"電力制度 新着情報 ({date.today().isoformat()})\n"]

    if alert:
        lines += [SEP, f"⚠ 要注意：一般送配電事業者 システム変更の可能性あり（{len(alert)}件）", SEP, ""]
        for item in alert:
            lines += _format_item(item)

    if normal:
        lines += [SEP, f"■ その他の新着情報（{len(normal)}件）", SEP, ""]
        for item in normal:
            lines += _format_item(item)

    return "\n".join(lines)


def send_mail(items: list[dict]) -> None:
    from_addr = os.environ["GMAIL_FROM"]
    to_addrs = [a.strip() for a in os.environ["GMAIL_TO"].split(",") if a.strip()]
    password = os.environ["GMAIL_APP_PASSWORD"]

    alert_count = sum(1 for i in items if i.get("requires_attention"))
    if alert_count:
        subject = f"[電力制度] ⚠要注意{alert_count}件 / 新着{len(items)}件 ({date.today().isoformat()})"
    else:
        subject = f"[電力制度] 新着 {len(items)} 件 ({date.today().isoformat()})"
    body = _build_body(items)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())

    logger.info("Mail sent to %s (%d items)", ", ".join(to_addrs), len(items))
