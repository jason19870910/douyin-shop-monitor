"""Unified configuration using pydantic-settings.

This module replaces the scattered configuration across:
- config.py (legacy Config class)
- .env (environment variables)
- Dockerfile (ENV directives)
- docker-compose.yml (environment sections)

All configuration is now centralized in the Settings class with proper
type validation, default values, and Docker secret support.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(secret_name: str, env_var: str = None, default: str = '') -> str:
    """Read secret from Docker secret file, then environment variable, then default.
    
    Docker secrets are mounted at /run/secrets/<secret_name>
    """
    # Try Docker secret file first
    secret_path = Path(f'/run/secrets/{secret_name}')
    if secret_path.exists():
        try:
            return secret_path.read_text().strip()
        except Exception:
            pass
    
    # Fall back to environment variable
    if env_var:
        return os.getenv(env_var, default)
    
    return default


def _read_secret_int(secret_name: str, env_var: str = None, default: int = 0) -> int:
    """Read integer secret from Docker secret file or environment variable."""
    val = _read_secret(secret_name, env_var, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


class Settings(BaseSettings):
    """Unified application settings with pydantic-settings.
    
    All settings can be configured via:
    1. Docker secrets (highest priority) - mounted at /run/secrets/
    2. Environment variables
    3. .env file (loaded automatically)
    4. Default values (lowest priority)
    
    Usage:
        from config.settings import get_settings
        settings = get_settings()
        print(settings.DOUYIN_APP_ID)
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',
        populate_by_name=True,
    )
    
    # =========================================================================
    # 基础配置
    # =========================================================================
    DATA_DIR: str = Field(default='./data', description='数据存储目录（容器内映射为 /data）')
    SCHEDULE_INTERVAL_MINUTES: int = Field(default=60, description='定时任务间隔（分钟）')
    ALERT_EMAIL: str = Field(default='', description='告警通知邮箱')
    API_AUTH_TOKEN: str = Field(default='', description='API 认证 Token（用于内部服务间调用）')
    API_KEY: str = Field(default='', description='API 密钥（可选，用于 API 认证）')
    KEEP_ALIVE_TIMEOUT: int = Field(default=30, description='Keep-alive 超时（秒）')
    TIMEOUT: int = Field(default=30, description='请求超时（秒）')
    EXTERNAL_DATA_BASE_URL: str = Field(default='https://example.com/monitor', description='外部数据服务基础 URL（可选，预留扩展）')
    
    # =========================================================================
    # 抖音开放平台配置（OAuth 2.0）
    # =========================================================================
    DOUYIN_APP_ID: str = Field(default='', description='抖音开放平台 App ID')
    DOUYIN_APP_SECRET: str = Field(default='', description='抖音开放平台 App Secret')
    DOUYIN_ACCESS_TOKEN: str = Field(default='', description='抖音访问令牌')
    
    # =========================================================================
    # 双域名基础 URL（抖店/创作者中心）
    # =========================================================================
    FXG_BASE_URL: str = Field(default='https://fxg.jinritemai.com', description='抖店基础 URL')
    CREATOR_BASE_URL: str = Field(default='https://creator.douyin.com', description='创作者中心基础 URL')
    
    # =========================================================================
    # 公共请求头配置
    # =========================================================================
    USER_AGENT: str = Field(
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        description='公共请求头中的 User-Agent'
    )
    
    # =========================================================================
    # 认证与签名参数（强时效性，需定期手动更新，通常 2h-7 天失效）
    # 获取方式：浏览器登录目标网站 -> F12 Network -> 任意请求 -> Request Headers
    # =========================================================================
    # 抖店签名参数
    TOKEN: str = Field(default='', description='抖店 __TOKEN 参数')
    MS_TOKEN: str = Field(default='', description='抖店 MS_TOKEN 参数')
    A_BOGUS: str = Field(default='', description='抖店 a_bogus 参数')
    VERIFY_FP: str = Field(default='', description='抖店 verifyFp 参数')
    FP: str = Field(default='', description='抖店 fp 参数')
    
    # =========================================================================
    # Cookie 配置（完整 Cookie 字符串，分号分隔）
    # 获取方法：浏览器登录 -> F12 -> Network -> 任意请求 -> Request Headers -> Cookie
    # =========================================================================
    FXG_COOKIES: str = Field(default='', description='抖店 Cookie (fxg.jinritemai.com)')
    CREATOR_COOKIES: str = Field(default='', description='创作者中心 Cookie (creator.douyin.com)')
    
    # =========================================================================
    # 抖店 Shop ID 与 Log ID（多店铺场景需配置）
    # =========================================================================
    FXG_SHOP_ID: int = Field(default=4272, description='抖店 Shop ID')
    FXG_LOG_ID: str = Field(default='104476165896', description='抖店 Log ID')
    FXG_PRODUCT_LID: str = Field(default='829906029528', description='抖店商品列表 _lid')
    FXG_ORDER_LID: str = Field(default='646601599070', description='抖店订单列表 _lid')
    FXG_ORDER_AID: int = Field(default=4272, description='抖店订单列表 aid')
    CREATOR_WORK_AID: int = Field(default=1128, description='创作者作品列表 aid')
    
    # =========================================================================
    # Celery / Redis 配置
    # =========================================================================
    CELERY_BROKER_URL: str = Field(default='redis://localhost:6379/0', description='Celery Broker URL')
    CELERY_RESULT_BACKEND: str = Field(default='redis://localhost:6379/0', description='Celery Result Backend URL')
    
    # =========================================================================
    # 创作者中心内容管理 API
    # =========================================================================
    CREATOR_WORK_LIST_URL: str = Field(
        default='https://creator.douyin.com/janus/douyin/creator/pc/work_list',
        description='创作者中心内容管理 API'
    )
    
    # =========================================================================
    # 告警配置
    # =========================================================================
    ALERT_WECOM_WEBHOOK: str = Field(default='', description='企业微信告警 Webhook')
    ALERT_DINGTALK_WEBHOOK: str = Field(default='', description='钉钉告警 Webhook')
    ALERT_SMTP_HOST: str = Field(default='', description='SMTP 服务器地址')
    ALERT_SMTP_PORT: int = Field(default=587, description='SMTP 端口')
    ALERT_SMTP_USER: str = Field(default='', description='SMTP 用户名')
    ALERT_SMTP_PASSWORD: str = Field(default='', description='SMTP 密码')
    ALERT_SMTP_FROM: str = Field(default='', description='SMTP 发件人邮箱')
    
    # =========================================================================
    # 日志配置
    # =========================================================================
    LOG_LEVEL: str = Field(default='DEBUG', description='日志级别')
    LOG_FILE: str = Field(default='logs/app.log', description='日志文件路径')
    LOG_MAX_BYTES: int = Field(default=10485760, description='单个日志文件最大字节数 (10MB)')
    LOG_BACKUP_COUNT: int = Field(default=5, description='日志备份文件数量')
    
    # =========================================================================
    # 监控配置
    # =========================================================================
    ENABLE_METRICS: bool = Field(default=True, description='是否启用 Prometheus 指标')
    METRICS_PORT: int = Field(default=9090, description='Prometheus 指标端口')
    
    # =========================================================================
    # 计算属性
    # =========================================================================
    @computed_field
    @property
    def COMMON_HEADERS(self) -> Dict[str, str]:
        """公共请求头模板（可根据需求覆盖）"""
        return {
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Priority": "u=1, i",
            "User-Agent": self.USER_AGENT
        }
    
    @computed_field
    @property
    def data_dir_path(self) -> Path:
        """数据目录的 Path 对象"""
        return Path(self.DATA_DIR)
    
    # =========================================================================
    # 字段验证器 - 从 Docker secrets 读取敏感配置
    # =========================================================================
    @field_validator('DOUYIN_APP_ID', mode='before')
    @classmethod
    def _load_douyin_app_id(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('douyin_app_id', 'DOUYIN_APP_ID')
    
    @field_validator('DOUYIN_APP_SECRET', mode='before')
    @classmethod
    def _load_douyin_app_secret(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('douyin_app_secret', 'DOUYIN_APP_SECRET')
    
    @field_validator('DOUYIN_ACCESS_TOKEN', mode='before')
    @classmethod
    def _load_douyin_access_token(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('douyin_access_token', 'DOUYIN_ACCESS_TOKEN')
    
    @field_validator('API_KEY', mode='before')
    @classmethod
    def _load_api_key(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('api_key', 'API_KEY')
    
    @field_validator('FXG_COOKIES', mode='before')
    @classmethod
    def _load_fxg_cookies(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('fxg_cookies', 'FXG_COOKIES')
    
    @field_validator('CREATOR_COOKIES', mode='before')
    @classmethod
    def _load_creator_cookies(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('creator_cookies', 'CREATOR_COOKIES')
    
    @field_validator('TOKEN', mode='before')
    @classmethod
    def _load_token(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('token', '__TOKEN')
    
    @field_validator('MS_TOKEN', mode='before')
    @classmethod
    def _load_ms_token(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('ms_token', 'MS_TOKEN')
    
    @field_validator('A_BOGUS', mode='before')
    @classmethod
    def _load_a_bogus(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('a_bogus', 'a_bogus')
    
    @field_validator('VERIFY_FP', mode='before')
    @classmethod
    def _load_verify_fp(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('verify_fp', 'verifyFp')
    
    @field_validator('FP', mode='before')
    @classmethod
    def _load_fp(cls, v: str) -> str:
        if v:
            return v
        return _read_secret('fp', 'fp')
    
    @field_validator('FXG_SHOP_ID', mode='before')
    @classmethod
    def _load_fxg_shop_id(cls, v: int) -> int:
        if v != 4272:  # 非默认值，直接返回
            return v
        return _read_secret_int('fxg_shop_id', 'FXG_SHOP_ID', 4272)
    
    @field_validator('FXG_LOG_ID', mode='before')
    @classmethod
    def _load_fxg_log_id(cls, v: str) -> str:
        if v != '104476165896':  # 非默认值，直接返回
            return v
        return _read_secret('fxg_log_id', 'FXG_LOG_ID', '104476165896')


# Singleton pattern for settings
_settings_instance: Optional[Settings] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get singleton Settings instance.
    
    Uses lru_cache to ensure only one instance is created.
    The Settings class reads from environment variables and Docker secrets
    automatically on instantiation.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# For backwards compatibility with existing code that uses Config class
class Config:
    """Backwards compatibility wrapper exposing expected attributes for Flask app.
    
    This class delegates to the Settings singleton to provide the same interface
    as the old config.py Config class.
    """
    
    def __getattr__(self, name: str) -> Any:
        settings = get_settings()
        if hasattr(settings, name):
            return getattr(settings, name)
        raise AttributeError(f"'Config' object has no attribute '{name}'")


# Global Config instance for backwards compatibility
Config = Config()