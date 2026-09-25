"""
Migration V001: Initial Schema
Create initial database schema for the monitoring platform.

Run: python -m migrations migrate
"""
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration - create initial schema."""
    logger.info("Applying migration V001: Initial Schema")
    
    # This migration creates the initial database structure
    # For JSON file backend, we initialize the data structure
    
    from services.fetcher import cache, CACHE_KEYS, DEFAULT_VIDEOS, DEFAULT_ACCOUNTS, DEFAULT_COMPLIANCE, DEFAULT_MEDIA, DEFAULT_AUTH_CONFIG
    
    # Initialize all cache keys with empty defaults if not present
    defaults = {
        'products': [],
        'orders': [],
        'creators': [],
        'videos': DEFAULT_VIDEOS,
        'accounts': DEFAULT_ACCOUNTS,
        'compliance_rules': DEFAULT_COMPLIANCE,
        'compliance_logs': [],
        'media': DEFAULT_MEDIA,
        'auth': DEFAULT_AUTH_CONFIG,
        'creator_works': [],
        'alert_config': {
            'sales_drop_threshold': 0.3,
            'conversion_drop_threshold': 0.2,
            'inventory_low_threshold': 10,
            'notification_email': '',
            'enabled': True
        },
        'alert_douyin_config': {
            'video_view_drop_threshold': 0.3,
            'video_like_drop_threshold': 0.2,
            'creator_follower_drop_threshold': 0.1,
            'notification_email': '',
            'enabled': True
        },
        'alert_dian_config': {
            'product_sales_drop_threshold': 0.3,
            'order_refund_rate_threshold': 0.15,
            'compliance_risk_threshold': 'medium',
            'notification_email': '',
            'enabled': True
        },
        'auth_config': DEFAULT_AUTH_CONFIG,
    }
    
    for key, default_value in defaults.items():
        if cache.get(CACHE_KEYS.get(key, key)) is None:
            cache.set(CACHE_KEYS.get(key, key), default_value)
            logger.info(f"Initialized cache key: {key}")
    
    # Initialize compliance data
    from services.fetcher import init_compliance_data
    init_compliance_data()
    
    logger.info("Migration V001 completed - Initial schema created")


def downgrade():
    """Rollback migration - clear all data."""
    logger.info("Rolling back migration V001: Initial Schema")
    
    from services.fetcher import cache, CACHE_KEYS
    
    # Clear all cache keys
    keys_to_clear = [
        'products', 'orders', 'creators', 'videos', 'accounts',
        'compliance_rules', 'compliance_logs', 'media', 'auth',
        'creator_works', 'alert_config', 'alert_douyin_config',
        'alert_dian_config', 'auth_config', 'last_update'
    ]
    
    for key in keys_to_clear:
        cache_key = CACHE_KEYS.get(key, key)
        try:
            cache.delete(cache_key)
            logger.info(f"Cleared cache key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to clear {cache_key}: {e}")
    
    logger.info("Migration V001 rolled back - All data cleared")