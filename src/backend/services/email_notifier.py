"""SMTP 邮件通知服务 - 用于告警和系统事件发送。

支持 SMTP 协议发送邮件通知。
配置：MAIL_HOST, MAIL_PORT, MAIL_USER, MAIL_PASSWORD, MAIL_FROM, MAIL_TO 环境变量
"""

import os
import smtplib
import email.message
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# SMTP 服务器配置 - 从环境变量读取
MAIL_HOST = os.getenv("MAIL_HOST", "smtp.qq.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "465"))  # SSL 端口
MAIL_USER = os.getenv("MAIL_USER", "262368285@qq.com")  # 用户提供的邮箱
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")  # SMTP 密码/授权码
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USER)
MAIL_TO = os.getenv("MAIL_TO", "")  # 接收者，多个用逗号分隔
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "true").lower() == "true"


def _get_recipients() -> List[str]:
    """解析邮件接收者地址。
    
    Returns:
        接收者邮件地址列表
    """
    if MAIL_TO:
        return [addr.strip() for addr in MAIL_TO.split(",") if addr.strip()]
    return []


def send_mail(subject: str, content: str, html_content: str = None, 
              recipients: List[str] = None) -> Dict[str, Any]:
    """发送邮件。
    
    Args:
        subject: 邮件主题
        content: 纯文本内容
        html_content: HTML 格式内容（可选）
        recipients: 接收者列表（可选，使用配置中的 MAIL_TO）
    
    Returns:
        发送结果字典 {'success': bool, 'message': str}
    """
    recipients = recipients or _get_recipients()
    
    if not recipients:
        logger.warning("没有配置邮件接收者，邮件已跳过发送")
        return {"success": False, "message": "No recipients configured"}
    
    try:
        msg = email.message.EmailMessage()
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = ", ".join(recipients)
        
        # 添加正文
        if html_content:
            msg.set_content(content)
            msg.add_alternative(html_content, subtype="html")
        else:
            msg.set_content(content)
        
        # 连接 SMTP 服务器
        if MAIL_USE_SSL:
            server = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        elif MAIL_USE_TLS:
            server = smtplib.SMTP(MAIL_HOST, MAIL_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(MAIL_HOST, MAIL_PORT)
        
        # 登录并发送
        server.login(MAIL_USER, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"邮件发送成功: {subject} -> {', '.join(recipients)}")
        return {"success": True, "message": f"Email sent to {len(recipients)} recipient(s)"}
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP 认证失败: {e}")
        return {"success": False, "message": f"SMTP authentication failed: {str(e)}"}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP 错误: {e}")
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"发送邮件时发生意外错误: {e}")
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


def send_alert_email(alert_type: str, title: str, content: str, 
                     level: str = "warning", html: bool = True) -> Dict[str, Any]:
    """发送告警邮件。
    
    专为告警系统设计，根据级别设置不同的主题前缀和颜色提示。
    
    Args:
        alert_type: 告警类型
        title: 告警标题
        content: 告警正文
        level: 告警级别 ("info", "warning", "error", "critical")
        html: 是否使用 HTML 格式
    
    Returns:
        发送结果字典
    """
    # 级别对应的主题前缀和颜色提示
    level_config = {
        "info": ("信息通知", "这是一条信息级别的告警"),
        "warning": ("警告通知", "注意查看相关事项"),
        "error": ("错误通知", "需要立即处理的错误"),
        "critical": ("紧急通知", "系统关键错误，需要立即关注")
    }
    
    level_subject_prefix, level_description = level_config.get(level, level_config["warning"])
    
    subject = f"[{level_subject_prefix}] {title}"
    
    # 构建 HTML 邮件内容
    html_body = f"""
    <html>
    <body>
        <h2>{level_subject_prefix}: {title}</h2>
        <p><strong>告警级别:</strong> {level}</p>
        <p><strong>发生时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>{content}</p>
        <hr>
        <p><small>此邮件由抖音监控系统自动发送</small></p>
    </body>
    </html>
    """
    
    text_body = f"""
    {level_subject_prefix}: {title}
    
    告警级别: {level}
    发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    {content}
    
    ---
    此邮件由抖音监控系统自动发送
    """
    
    return send_mail(subject, text_body, html_content=html_body, recipients=_get_recipients())


def send_system_health_email(status: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """发送系统健康状态邮件。
    
    Args:
        status: 状态 ("healthy", "degraded", "unhealthy")
        details: 健康检查详细信息字典
    
    Returns:
        发送结果字典
    """
    status_config = {
        "healthy": ("系统健康", "绿色", "系统运行正常，无需关注"),
        "degraded": ("系统轻度异常", "黄色", "系统出现轻度异常，建议及时处理"),
        "unhealthy": ("系统严重异常", "红色", "系统出现严重异常，需要立即处理")
    }
    
    emoji, color, description = status_config.get(status, status_config["degraded"])
    
    detail_lines = []
    for key, value in details.items():
        detail_lines.append(f"- **{key}**: {value}")
    
    html_content = f"""
    <html>
    <body>
        <h2>{emoji} {emoji} 系统状态: {emoji}</h2>
        <p><strong>状态:</strong> {status}</p>
        <p><strong>描述:</strong> {description}</p>
        <p><strong>检查时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p><strong>详细信息:</strong></p>
        <ul>
        {''.join([f"<li>{line}</li>" for line in detail_lines])}
        </ul>
        <p><small>此邮件由抖音监控系统自动发送</small></p>
    </body>
    </html>
    """
    
    text_content = f"""
    系统状态: {status}
    检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    详细信息:
    {''.join([f"- {key}: {value}" for key, value in details.items()])}
    
    ---
    此邮件由抖音监控系统自动发送
    """
    
    subject = f"[{emoji} {status}] 系统健康检查结果"
    return send_mail(subject, text_content, html_content=html_content)


# 测试发送功能
def test_email_connection() -> Dict[str, Any]:
    """测试 SMTP 连接是否正常。
    
    Returns:
        测试结果字典
    """
    try:
        result = send_mail(
            subject="🔧 系统测试 - 邮件服务连接测试",
            content="如果您收到此邮件，说明 SMTP 邮件服务配置成功。",
            html_content="<h3>🔧 系统测试</h3><p>如果您收到此邮件，说明 SMTP 邮件服务配置成功。</p>"
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"Test failed: {str(e)}"}


# 导出主要接口
__all__ = [
    "send_mail",
    "send_alert_email",
    "send_system_health_email",
    "test_email_connection",
    "MAIL_HOST",
    "MAIL_PORT", 
    "MAIL_USER",
    "MAIL_FROM",
    "MAIL_TO"
]