"""Pydantic models for data validation."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


logger = logging.getLogger(__name__)


class ProductStatus(str, Enum):
    ON_SALE = "on_sale"
    OFF_SALE = "off_sale"
    OUT_OF_STOCK = "out_of_stock"


class OrderStatus(str, Enum):
    PENDING = "pending"
    WAIT_PAY = "wait_pay"
    WAIT_SEND = "wait_send"
    SENT = "sent"
    DONE = "done"
    CLOSED = "closed"
    AFTER_SALE = "after_sale"
    ABNORMAL = "abnormal"
    TIMEOUT_SEND = "timeout_send"
    URGENT_SEND = "urgent_send"
    COMPLETED = "completed"
    SHIPPED = "shipped"


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Product(BaseModel):
    """Product data model."""
    product_id: str
    product_name: str
    category: Optional[str] = None
    price: float = 0.0
    sales_today: int = 0
    sales_yesterday: int = 0
    inventory: int = 0
    conversion_rate: float = 0.0
    conversion_rate_today: float = 0.0
    conversion_rate_yesterday: float = 0.0
    status: Optional[ProductStatus] = None
    fetched_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Allow extra fields from API
    model_config = {"extra": "allow"}


class Order(BaseModel):
    """Order data model."""
    order_id: str
    product_name: Optional[str] = None
    product_id: Optional[str] = None
    amount: float = 0.0
    status: Optional[OrderStatus] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None
    buyer_id: Optional[str] = None
    buyer_name: Optional[str] = None
    quantity: int = 1
    fetched_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class Creator(BaseModel):
    """Creator data model."""
    creator_id: str
    creator_name: str
    follower_count: int = 0
    following_count: int = 0
    video_count: int = 0
    total_likes: int = 0
    category: Optional[str] = None
    level: Optional[str] = None
    fetched_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class Video(BaseModel):
    """Video data model."""
    video_id: str
    title: str
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    duration: int = 0
    create_time: Optional[str] = None
    status: Optional[str] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    fetched_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class Account(BaseModel):
    """Account data model."""
    account_id: str
    account_name: str
    platform: str = "douyin"
    status: Optional[str] = None
    follower_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class ComplianceRule(BaseModel):
    """Compliance rule data model."""
    id: str
    rule_name: str
    rule_type: str
    rule_content: Dict[str, Any] = {}
    severity: str = "MEDIUM"
    category: str = "通用"
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class ComplianceLog(BaseModel):
    """Compliance check log model."""
    id: str
    rule_id: str
    target_type: str  # product, video, creator, etc.
    target_id: str
    target_name: Optional[str] = None
    status: str  # pass, fail, warning
    details: Dict[str, Any] = {}
    checked_at: str
    
    model_config = {"extra": "allow"}


class Media(BaseModel):
    """Media data model."""
    media_id: str
    title: str
    type: str  # image, video, document
    url: str
    status: str = "active"
    size: int = 0
    mime_type: Optional[str] = None
    created_at: Optional[str] = None
    
    model_config = {"extra": "allow"}


class AuthConfig(BaseModel):
    """Authentication configuration model."""
    douyin_app_id: str = ""
    douyin_app_secret: str = ""
    redirect_uri: str = ""
    authorized: bool = False
    access_token: str = ""
    refresh_token: str = ""
    expires_at: int = 0
    scope: List[str] = []
    
    model_config = {"extra": "allow"}


class AlertConfig(BaseModel):
    """Alert configuration model."""
    sales_drop_threshold: float = 0.3
    conversion_drop_threshold: float = 0.2
    inventory_low_threshold: int = 10
    notification_email: str = ""
    enabled: bool = True
    
    model_config = {"extra": "allow"}


class AlertDouyinConfig(BaseModel):
    """Douyin-specific alert configuration model."""
    video_view_drop_threshold: float = 0.3
    video_like_drop_threshold: float = 0.2
    creator_follower_drop_threshold: float = 0.1
    notification_email: str = ""
    enabled: bool = True
    
    model_config = {"extra": "allow"}


class AlertDianConfig(BaseModel):
    """Dian-specific alert configuration model."""
    product_sales_drop_threshold: float = 0.3
    order_refund_rate_threshold: float = 0.15
    compliance_risk_threshold: str = "medium"
    notification_email: str = ""
    enabled: bool = True
    
    model_config = {"extra": "allow"}


# Model mapping for validation
MODEL_MAP = {
    'products': Product,
    'orders': Order,
    'creators': Creator,
    'videos': Video,
    'accounts': Account,
    'compliance_rules': ComplianceRule,
    'compliance_logs': ComplianceLog,
    'media': Media,
    'auth': AuthConfig,
    'alert_config': AlertConfig,
    'alert_douyin_config': AlertDouyinConfig,
    'alert_dian_config': AlertDianConfig,
}


def validate_data(data: List[Dict], model_type: str) -> List[Dict]:
    """Validate list of dicts against Pydantic model.
    
    Args:
        data: List of dictionaries to validate
        model_type: Key in MODEL_MAP
        
    Returns:
        List of validated dictionaries (converted from models)
    """
    model_class = MODEL_MAP.get(model_type)
    if not model_class:
        return data  # No model defined, return as-is
    
    validated = []
    for item in data:
        try:
            # Validate and convert to dict
            model_instance = model_class.model_validate(item)
            validated.append(model_instance.model_dump(exclude_none=False))
        except Exception as e:
            logger.warning(f"Validation failed for {model_type} item: {e}, keeping original")
            validated.append(item)
    
    return validated


def validate_single(data: Dict, model_type: str) -> Dict:
    """Validate single dict against Pydantic model."""
    model_class = MODEL_MAP.get(model_type)
    if not model_class:
        return data
    
    try:
        model_instance = model_class.model_validate(data)
        return model_instance.model_dump(exclude_none=False)
    except Exception as e:
        logger.warning(f"Validation failed for {model_type}: {e}, keeping original")
        return data