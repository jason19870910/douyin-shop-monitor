"""Pytest configuration and shared fixtures."""

import pytest
import os
import sys
from pathlib import Path

# Add backend source directory to path
project_root = Path(__file__).parent.parent.parent  # /opt/douyin-platform
backend_dir = project_root / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ['DEBUG'] = 'true'
os.environ['API_KEY'] = 'test_api_key_for_testing'


@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        'api_key': 'test_api_key_for_testing',
        'debug': True,
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset rule engine
    from services.rule_engine import reset_rule_engine
    reset_rule_engine()
    
    # Reset douyin signer
    import douyin_sign
    douyin_sign._default_signer = None
    
    # Reset alert manager
    import alerts
    alerts.alert_manager = alerts.AlertManager()
    
    yield
    
    # Cleanup after test
    reset_rule_engine()
    douyin_sign._default_signer = None
    alerts.alert_manager = alerts.AlertManager()


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache for testing."""
    from unittest.mock import MagicMock
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    return mock_cache


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return [
        {
            'product_id': 'p1',
            'product_name': 'Test Product 1',
            'category': 'Electronics',
            'price': 99.99,
            'sales_today': 10,
            'sales_yesterday': 5,
            'inventory': 100,
            'conversion_rate': 0.05,
            'status': 'on_sale'
        },
        {
            'product_id': 'p2',
            'product_name': 'Test Product 2',
            'category': 'Clothing',
            'price': 49.99,
            'sales_today': 20,
            'sales_yesterday': 15,
            'inventory': 50,
            'conversion_rate': 0.08,
            'status': 'on_sale'
        }
    ]


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return [
        {
            'order_id': 'o1',
            'product_id': 'p1',
            'product_name': 'Test Product',
            'amount': 99.99,
            'status': 'done',
            'create_time': '2024-01-01T10:00:00',
            'buyer_id': 'b1'
        },
        {
            'order_id': 'o2',
            'product_id': 'p2',
            'product_name': 'Another Product',
            'amount': 49.99,
            'status': 'wait_send',
            'create_time': '2024-01-01T11:00:00',
            'buyer_id': 'b2'
        }
    ]


@pytest.fixture
def sample_creator_data():
    """Sample creator data for testing."""
    return [
        {
            'creator_id': 'c1',
            'creator_name': 'Creator One',
            'follower_count': 10000,
            'video_count': 50,
            'category': 'Tech'
        },
        {
            'creator_id': 'c2',
            'creator_name': 'Creator Two',
            'follower_count': 5000,
            'video_count': 30,
            'category': 'Lifestyle'
        }
    ]


@pytest.fixture
def sample_compliance_rules():
    """Sample compliance rules for testing."""
    return [
        {
            'id': 'r1',
            'rule_name': 'Keyword Rule',
            'rule_type': 'KEYWORD',
            'rule_content': {'keywords': ['违规', '禁止'], 'fields': ['product_name']},
            'severity': 'HIGH',
            'category': '广告法',
            'enabled': True
        },
        {
            'id': 'r2',
            'rule_name': 'Regex Rule',
            'rule_type': 'REGEX',
            'rule_content': {'patterns': [r'\d{10,}'], 'fields': ['description']},
            'severity': 'MEDIUM',
            'category': '隐私保护',
            'enabled': True
        }
    ]


# Pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (mocked external services)")
    config.addinivalue_line("markers", "contract: API contract tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection - add markers based on path."""
    for item in items:
        # Auto-mark based on test path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)