"""Blueprints package initialization."""
from blueprints.products import products_bp
from blueprints.orders import orders_bp
from blueprints.creators import creators_bp
from blueprints.auth import auth_bp
from blueprints.videos import videos_bp
from blueprints.accounts import accounts_bp
from blueprints.compliance import compliance_bp
from blueprints.media import media_bp
from blueprints.alerts import alerts_bp
from blueprints.dashboard import dashboard_bp
from blueprints.frontend import frontend_bp

__all__ = [
    'products_bp',
    'orders_bp',
    'creators_bp',
    'auth_bp',
    'videos_bp',
    'accounts_bp',
    'compliance_bp',
    'media_bp',
    'alerts_bp',
    'dashboard_bp',
    'frontend_bp',
]