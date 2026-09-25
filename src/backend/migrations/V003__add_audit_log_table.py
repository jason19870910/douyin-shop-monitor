"""
Migration V003: add_audit_log_table
Initialize audit log storage for JSON/Redis backend.

Run: python -m migrations
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration - initialize audit_log cache key and persist empty list."""
    logger.info("Applying migration V003: add_audit_log_table")

    from services.fetcher import cache, CACHE_KEYS, save_json_file, DATA_DIR

    # Ensure CACHE_KEYS has audit_log (migration-safe even if older code paths miss it)
    if 'audit_log' not in CACHE_KEYS:
        CACHE_KEYS['audit_log'] = 'audit_log'

    existing = cache.get(CACHE_KEYS['audit_log'])
    if existing is None:
        cache.set(CACHE_KEYS['audit_log'], [])
        logger.info("Initialized cache key: audit_log")
    elif not isinstance(existing, list):
        cache.set(CACHE_KEYS['audit_log'], [])
        logger.warning("Reset non-list audit_log value to empty list")

    audit_file = DATA_DIR / 'audit_log.json'
    if not audit_file.exists():
        save_json_file(audit_file, [])
        logger.info("Created audit_log.json at %s", audit_file)

    # Seed a bootstrap marker so operators can verify migration ran
    marker = {
        'id': 'migration-v003',
        'action': 'schema.init',
        'actor': 'system',
        'resource_type': 'audit_log',
        'resource_id': 'audit_log',
        'details': {'migration': 'V003', 'message': 'audit log storage initialized'},
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    logs = cache.get(CACHE_KEYS['audit_log'], [])
    if not any(isinstance(x, dict) and x.get('id') == 'migration-v003' for x in logs):
        logs.insert(0, marker)
        cache.set(CACHE_KEYS['audit_log'], logs)
        save_json_file(audit_file, logs)

    logger.info("Migration V003 completed")


def downgrade():
    """Rollback migration - clear audit_log storage."""
    logger.info("Rolling back migration V003: add_audit_log_table")

    from services.fetcher import cache, CACHE_KEYS, DATA_DIR

    key = CACHE_KEYS.get('audit_log', 'audit_log')
    try:
        cache.delete(key)
    except Exception:
        cache.set(key, None)

    audit_file = DATA_DIR / 'audit_log.json'
    if audit_file.exists():
        try:
            audit_file.unlink()
        except OSError as e:
            logger.warning("Failed to remove %s: %s", audit_file, e)

    logger.info("Migration V003 rolled back")
