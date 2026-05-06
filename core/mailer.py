import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _build_body(items: list[dict]) -> str:
    lines = [f"電力制度 新着情報 ({date.today().isoformat()})\n"]
    for item in items:
        lines.append(f"【{item['site_name']}】 {item['title']}")
        lines.append(f"URL: {item['url']}")
        if item.get("summary"):
            lines.append(f"概要: {item['summary']}")
        lines.append("")
    return "\n".join(lines)


def send_mail(items: list[dict]) -> None:
    from_addr = os.environ["GMAIL_FROM"]
    to_addrs = [a.strip() for a in os.environ["GMAIL_TO"].split(",") if a.strip()]
    password = os.environ["GMAIL_APP_PASSWORD"]

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
