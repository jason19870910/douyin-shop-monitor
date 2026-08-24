"""
Migration V003: add_audit_log_table
Add Audit Log Table

Run: python -m migrations.migrate
"""
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration."""
    logger.info(f"Applying migration V003: add_audit_log_table")
    # TODO: Add your upgrade logic here
    # Example:
    # from services.fetcher import cache, CACHE_KEYS
    # cache.set(CACHE_KEYS['new_key'], [])
    
    logger.info(f"Migration V003 completed")


def downgrade():
    """Rollback migration."""
    logger.info(f"Rolling back migration V003: add_audit_log_table")
    # TODO: Add your rollback logic here
    # Example:
    # from services.fetcher import cache, CACHE_KEYS
    # cache.delete(CACHE_KEYS['new_key'])
    
    logger.info(f"Migration V003 rolled back")
