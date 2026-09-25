"""Alert notification dispatchers (WeChat Work webhook + email)."""
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

# WeChat Work webhook URL (from env or config)
WECHAT_WEBHOOK_URL = os.getenv(
    'WECHAT_WEBHOOK_URL',
    'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4b6598f0-5864-49da-b185-f864c25241d6'
)

# Email SMTP config (from env)
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')


def _format_alert_text(alert: Dict[str, Any]) -> str:
    """Format alert dict to human-readable text for notifications."""
    alert_type = alert.get('type', 'unknown')
    product_name = alert.get('product_name', '')
    message = alert.get('message', '')
    timestamp = alert.get('timestamp', '')
    drop_rate = alert.get('drop_rate')
    inventory = alert.get('inventory')
    threshold = alert.get('threshold')

    lines = [f'【告警通知】{alert_type}']
    lines.append(f'商品: {product_name}')
    lines.append(f'详情: {message}')
    if drop_rate is not None:
        lines.append(f'下降幅度: {drop_rate:.1%}')
    if inventory is not None:
        lines.append(f'当前库存: {inventory}')
    if threshold is not None:
        lines.append(f'阈值: {threshold}')
    lines.append(f'时间: {timestamp}')
    return '\n'.join(lines)


def send_wechat_notification(alert: Dict[str, Any]) -> bool:
    """Send alert to WeChat Work group via webhook.

    Args:
        alert: Alert dict with type, message, product_name, etc.

    Returns:
        True if sent successfully, False otherwise.
    """
    if not WECHAT_WEBHOOK_URL:
        logger.warning('WeChat webhook URL not configured, skipping')
        return False

    text = _format_alert_text(alert)

    # Map alert type to mentioned severity
    alert_type = alert.get('type', '')
    severity_map = {
        'sales_drop': 'warning',
        'low_inventory': 'warning',
        'conversion_drop': 'warning',
    }
    severity = severity_map.get(alert_type, 'info')

    payload = {
        'msgtype': 'markdown',
        'markdown': {
            'content': (
                f'{"<font color="warning">" if severity == "warning" else "<font color="info">"}'
                f'{text}'
                f'</font>'
            )
        }
    }

    try:
        resp = requests.post(
            WECHAT_WEBHOOK_URL,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'},
        )
        data = resp.json()
        if data.get('errcode') == 0:
            logger.info(f'WeChat notification sent for alert: {alert.get("type")}')
            return True
        logger.error(f'WeChat webhook error: {data}')
        return False
    except Exception as e:
        logger.error(f'Failed to send WeChat notification: {e}')
        return False


def send_email_notification(
    alert: Dict[str, Any],
    to_email: Optional[str] = None,
) -> bool:
    """Send alert via email.

    Args:
        alert: Alert dict with type, message, etc.
        to_email: Recipient email. If None, uses SMTP_FROM.

    Returns:
        True if sent successfully, False otherwise.
    """
    if not SMTP_HOST or not SMTP_USER:
        logger.debug('SMTP not configured, skipping email notification')
        return False

    recipient = to_email or SMTP_FROM
    if not recipient:
        logger.warning('No email recipient configured, skipping')
        return False

    text = _format_alert_text(alert)
    subject = f'[告警] {alert.get("type", "unknown")} - {alert.get("product_name", "")}'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM or SMTP_USER
    msg['To'] = recipient
    msg.attach(MIMEText(text, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM or SMTP_USER, [recipient], msg.as_string())
        logger.info(f'Alert email sent to {recipient}: {alert.get("type")}')
        return True
    except Exception as e:
        logger.error(f'Failed to send alert email: {e}')
        return False


def send_alert_notification(
    alert: Dict[str, Any],
    email: Optional[str] = None,
) -> None:
    """Dispatch alert notification via all configured channels.

    This is the main entry point called by the alert checker.
    Sends to WeChat Work webhook (always) and email (if configured).

    Args:
        alert: Alert dict with type, message, product_name, timestamp, etc.
        email: Optional override recipient email.
    """
    # WeChat Work (always attempt - URL is hardcoded default)
    send_wechat_notification(alert)

    # Email (only if SMTP configured)
    if email or (SMTP_HOST and SMTP_USER):
        send_email_notification(alert, to_email=email)
