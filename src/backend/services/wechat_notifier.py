"""企业微信通知服务 - 用于告警和系统事件推送。

使用企业微科机器人 Webhook 发送消息到企业微信群/个人。
配置：WEBHOOK_URL 环境变量
"""

import json
import os
import requests
from typing import Dict, Any, List, Optional

# 企业微信机器人 Webhook URL (从环境变量读取，默认使用用户提供的)
WEBHOOK_URL = os.getenv(
    "WECHAT_WEBHOOK_URL", 
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=08aa87f3-b150-4120-a0b7-f498309f223d"
)

# 从环境变量读取配置
WEBHOOK_SECRET = os.getenv("WECHAT_WEBHOOK_SECRET", "")


def send_markdown_message(title: str, content: str, mentioned_list: List[str] = None, mentioned_watch_list: List[str] = None) -> Dict[str, Any]:
    """发送 markdown 格式的企业微信消息。
    
    Args:
        title: 消息标题
        content: markdown 内容
        mentioned_list: @ 的开放列表（可选）
        mentioned_watch_list: 关注的开放列表（可选）
    
    Returns:
        企业微信 API 返回的结果字典
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "content": content
        }
    }
    
    if mentioned_list:
        payload["markdown"]["mentioned_list"] = mentioned_list
    if mentioned_watch_list:
        payload["markdown"]["mentioned_watch_list"] = mentioned_watch_list
    
    try:
        response = requests.post(Webhook_URL, json=payload, timeout=10)
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"企业微信发送失败: {e}")
        return {"errcode": -1, "errmsg": str(e)}


def send_text_message(text: str, mentioned_list: List[str] = None) -> Dict[str, Any]:
    """发送文本格式的企业微信消息。
    
    Args:
        text: 文本内容
        mentioned_list: @ 的开放列表（可选）
    
    Returns:
        企业微信 API 返回的结果字典
    """
    payload = {
        "msgtype": "text",
        "text": {
            "content": text
        }
    }
    
    if mentioned_list:
        payload["text"]["mentioned_list"] = mentioned_list
    
    try:
        response = requests.post(Webhook_URL, json=payload, timeout=10)
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"企业微信发送文本失败: {e}")
        return {"errcode": -1, "errmsg": str(e)}


def send_alert_notification(alert_type: str, title: str, content: str, level: str = "warning") -> Dict[str, Any]:
    """发送告警通知到企业微信。
    
    专为告警系统设计，根据级别选择不同的颜色和格式。
    
    Args:
        alert_type: 告警类型（如 "dian_alert", "douyin_alert", "compliance_check" 等）
        title: 告警标题
        content: 告警正文内容
        level: 告警级别 ("info", "warning", "error", "critical")
    
    Returns:
        企业微信 API 返回结果
    """
    # 根据级别设置颜色关键词
    level_keywords = {
        "info": "信息",
        "warning": "警告", 
        "error": "错误",
        "critical": "严重"
    }
    
    level_name = level_keywords.get(level, "警告")
    
    markdown_content = f"> **{alert_type}**\n"
    markdown_content += f"> **级别**: {level_name}\n"
    markdown_content += f"> **标题**: {title}\n"
    markdown_content += f"> **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown_content += f">\n"
    markdown_content += content
    
    return send_markdown_message(f"🔔 {alert_type} - {level_name}", markdown_content)


def notify_system_health(status: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """发送系统健康状态通知。
    
    Args:
        status: 状态 ("healthy", "degraded", "unhealthy")
        details: 健康检查详细信息字典
    
    Returns:
        企业微信 API 返回结果
    """
    status_emoji = {"healthy": "🟢", "degraded": "🟡", "unhealthy": "🔴"}
    status_text = {"healthy": "正常", "degraded": "轻度异常", "unhealthy": "严重异常"}
    
    emoji = status_emoji.get(status, "🟡")
    text = status_text.get(status, "未知状态")
    
    detail_content = ""
    for key, value in details.items():
        detail_content += f"- **{key}**: {value}\n"
    
    return send_markdown_message(
        f"{emoji} 系统健康状态 - {text}",
        f"> **状态**: {text}\n> **检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n> **详情**: \n{detail_content}"
    )


# 便捷函数：直接使用用户提供的 Webhook URL
WECHAT_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=08aa87f3-b150-4120-a0b7-f498309f223d"


def test_connection() -> bool:
    """测试企业微信 Webhook 连接是否可达。
    
    Returns:
        如果连接成功返回 True，失败返回 False
    """
    try:
        # 发送一个测试消息
        result = send_text_message("🔧 系统测试连接 - 告警通知服务")
        # 企业微信返回 errcode 为 0 表示成功
        return result.get("errcode") == 0
    except Exception:
        return False


# 导出便捷接口
__all__ = [
    "send_markdown_message",
    "send_text_message", 
    "send_alert_notification",
    "notify_system_health",
    "test_connection",
    "WECHAT_WEBHOOK_URL"
]